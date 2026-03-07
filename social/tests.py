from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import profile, Post, Comment

class SocialAppTests(TestCase):
    def create_user(self, username='alice', password='password'):
        user = User.objects.create_user(username=username, password=password)
        profile.objects.create(user=user, display_name=username)
        return user

    def test_register_and_login(self):
        # home page should redirect anonymous users to login
        resp = self.client.get(reverse('home'))
        self.assertRedirects(resp, reverse('login'))
        # login page should contain link to register
        resp = self.client.get(reverse('login'))
        self.assertContains(resp, 'Login to ConnectHub')
        self.assertContains(resp, 'Register here')
        # discover should require login
        resp = self.client.get(reverse('discover'))
        self.assertRedirects(resp, reverse('login') + '?next=' + reverse('discover'))
        # registration page contains criteria
        resp = self.client.get(reverse('register'))
        self.assertContains(resp, 'Your password must be at least 8 characters long')
        # now submit registration
        resp = self.client.post(reverse('register'), {
            'username': 'bob',
            'password1': 'secret123',
            'password2': 'secret123',
        })
        self.assertRedirects(resp, reverse('feed'))
        self.assertTrue(User.objects.filter(username='bob').exists())
        # login
        self.client.logout()
        login = self.client.post(reverse('login'), {
            'username': 'bob',
            'password': 'secret123'
        })
        self.assertEqual(login.status_code, 302)
        # test home page redirects authenticated users to feed
        resp = self.client.get(reverse('home'))
        self.assertRedirects(resp, reverse('feed'))
        # logout (using GET since button now a link) should redirect to home
        resp = self.client.get(reverse('logout'))
        self.assertRedirects(resp, reverse('home'))
        # after logout, home page should not redirect (user is anonymous)
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Welcome to ConnectHub')

    def test_profile_edit(self):
        user = self.create_user()
        self.client.login(username='alice', password='password')
        resp = self.client.post(reverse('my_profile'), {'display_name': 'Alice', 'bio': 'Hello'})
        self.assertRedirects(resp, reverse('my_profile'))
        user.refresh_from_db()
        self.assertEqual(user.profile.display_name, 'Alice')
        self.assertEqual(user.profile.bio, 'Hello')

    def test_create_like_comment_follow(self):
        a = self.create_user('a', 'pw')
        b = self.create_user('b', 'pw')
        self.client.login(username='a', password='pw')
        # create post
        resp = self.client.post(reverse('create_post'), {'content': 'hi there'})
        self.assertRedirects(resp, reverse('feed'))
        post = Post.objects.get(author=a)
        # verify feed shows counts and timesince and author info
        resp = self.client.get(reverse('feed'))
        self.assertContains(resp, 'Comments: 0')
        self.assertContains(resp, 'Likes: 0')
        self.assertContains(resp, 'ago')
        # should show username link and display name if set
        self.assertContains(resp, 'a href="/profile/a/"')
        # update profile display_name and check
        a.profile.display_name = 'Alpha'
        a.profile.save()
        resp = self.client.get(reverse('feed'))
        self.assertContains(resp, '(Alpha)')
        # like
        resp = self.client.post(reverse('like_post', args=[post.pk]))
        post.refresh_from_db()
        self.assertIn(a, post.likes.all())
        # feed should update like count
        resp = self.client.get(reverse('feed'))
        self.assertContains(resp, 'Likes: 1')
        # check profile page stats reflect current post
        resp = self.client.get(reverse('user_profile', args=[a.username]))
        self.assertContains(resp, 'Posts: 1')
        self.assertContains(resp, 'Followers: 0')
        self.assertContains(resp, 'Following: 0')
        # comment
        resp = self.client.post(reverse('add_comment', args=[post.pk]), {'content': 'nice'})
        self.assertRedirects(resp, reverse('feed'))
        comment = Comment.objects.get(post=post)
        self.assertEqual(comment.author, a)
        # feed should show comment count
        resp = self.client.get(reverse('feed'))
        self.assertContains(resp, 'Comments: 1')
        # delete comment
        resp = self.client.post(reverse('delete_comment', args=[comment.pk]))
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
        # follow/unfollow
        # follow with no referer header should default to 'home'
        resp = self.client.post(reverse('follow', args=[b.username]))
        self.assertRedirects(resp, reverse('home'))
        self.assertIn(b.profile, a.profile.following.all())
        # unfollow again
        resp = self.client.post(reverse('follow', args=[b.username]))
        self.assertRedirects(resp, reverse('home'))
        self.assertNotIn(b.profile, a.profile.following.all())

    def test_edit_post_window_and_permissions(self):
        # only author may edit and only within 15 minutes
        user = self.create_user('author', 'pw')
        other = self.create_user('other', 'pw')
        self.client.login(username='author', password='pw')
        post = Post.objects.create(author=user, content='original')

        # editing immediately should work
        resp = self.client.get(reverse('edit_post', args=[post.pk]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(reverse('edit_post', args=[post.pk]), {'content': 'updated'})
        self.assertRedirects(resp, reverse('feed'))
        post.refresh_from_db()
        self.assertEqual(post.content, 'updated')

        # simulate expiry by modifying created_at outside window
        from django.utils import timezone
        from datetime import timedelta
        post.created_at = timezone.now() - timedelta(minutes=16)
        post.save()

        # refresh feed and ensure edit link is no longer shown
        resp = self.client.get(reverse('feed'))
        self.assertNotContains(resp, 'Edit Post')

        resp = self.client.post(reverse('edit_post', args=[post.pk]), {'content': 'later'})
        self.assertRedirects(resp, reverse('feed'))
        post.refresh_from_db()
        # content should not have changed
        self.assertEqual(post.content, 'updated')

        # non-author cannot access
        self.client.logout()
        self.client.login(username='other', password='pw')
        resp = self.client.get(reverse('edit_post', args=[post.pk]))
        self.assertRedirects(resp, reverse('feed'))

    def test_suggested_users_section(self):
        # create a handful of users
        main = self.create_user('main', 'pw')
        others = [self.create_user(f'u{i}', 'pw') for i in range(1, 6)]

        # let main follow the first two
        main.profile.following.add(others[0].profile, others[1].profile)

        self.client.login(username='main', password='pw')
        resp = self.client.get(reverse('feed'))
        # users 1 and 2 should not appear in suggestions
        self.assertNotContains(resp, 'u1')
        self.assertNotContains(resp, 'u2')
        # the remaining three should appear (order may vary)
        self.assertContains(resp, 'u3')
        self.assertContains(resp, 'u4')
        self.assertContains(resp, 'u5')

        # follow a suggested user via the form button
        resp = self.client.post(reverse('follow', args=['u3']), HTTP_REFERER=reverse('feed'))
        self.assertRedirects(resp, reverse('feed'))
        self.assertIn(others[2].profile, main.profile.following.all())

        # after following u3, it should drop out of suggestions
        resp = self.client.get(reverse('feed'))
        self.assertNotContains(resp, 'u3')

    def test_search(self):
        u = self.create_user('searchuser', 'pw')
        self.client.login(username=u.username, password='pw')
        Post.objects.create(author=u, content='findme')
        resp = self.client.get(reverse('search') + '?q=find')
        self.assertContains(resp, 'searchuser')
        self.assertContains(resp, 'findme')

