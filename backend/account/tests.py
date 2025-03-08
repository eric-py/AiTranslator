from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

User = get_user_model()

class AccountTests(TestCase):
    def setUp(self):
        """Setup test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.home_url = reverse('account:home')
        self.login_url = reverse('account:login')
        self.register_url = reverse('account:register')
        self.profile_url = reverse('account:profile')
        self.password_change_url = reverse('account:password_change')
        self.email_change_url = reverse('account:email_change')
        self.delete_account_url = reverse('account:delete_account')
        self.password_reset_url = reverse('account:password_reset')
        self.password_reset_done_url = reverse('account:password_reset_done')
        self.password_reset_confirm_url = reverse('account:password_reset_confirm', kwargs={'uidb64': 'Mg', 'token': 'set-password'})

    def test_home_view(self):
        """Test home view for anonymous and authenticated users"""
        # Anonymous user should be able to access home
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/home.html')

        # Authenticated user should be redirected
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 302)

    def test_login_view_anonymous(self):
        """Test login view for anonymous users"""
        # Test GET request
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')

        # Test successful login
        # response = self.client.post(self.login_url, {
        #     'username': 'testuser',
        #     'password': 'testpass123'
        # })
        # self.assertRedirects(response, self.profile_url)

        # Test invalid login
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)


    def test_login_view_authenticated(self):
        """Test login view for authenticated users"""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Try to access login page
        response = self.client.get(self.login_url)
        self.assertRedirects(response, self.profile_url)

        # Try to post to login page
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, self.profile_url)

    def test_register_view(self):
        """Test registration functionality"""
        # Test GET request
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/register.html')

        # Test successful registration
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertRedirects(response, self.login_url)
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Test duplicate email registration
        response = self.client.post(self.register_url, {
            'username': 'anotheruser',
            'email': 'test@example.com',  # Already exists
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_profile_view(self):
        """Test profile view access"""
        # Unauthenticated user should be redirected to login
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f'{self.login_url}?next={self.profile_url}')

        # Authenticated user should access profile
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/profile.html')

    def test_password_change(self):
        """Test password change functionality"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test successful password change
        response = self.client.post(self.password_change_url, {
            'old_password': 'testpass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        })
        self.assertRedirects(response, self.profile_url)

        # Verify new password works
        self.assertTrue(
            self.client.login(username='testuser', password='newpass456')
        )

    def test_email_change(self):
        """Test email change functionality"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test successful email change
        response = self.client.post(self.email_change_url, {
            'new_email': 'newemail@example.com',
            'confirm_email': 'newemail@example.com'
        })
        self.assertRedirects(response, self.profile_url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')

        # Test mismatched emails
        response = self.client.post(self.email_change_url, {
            'new_email': 'another@example.com',
            'confirm_email': 'different@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['email_form'].errors)

    def test_delete_account(self):
        """Test account deletion"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET request should redirect
        response = self.client.get(self.delete_account_url)
        self.assertRedirects(response, self.profile_url)
        
        # Test successful deletion
        response = self.client.post(self.delete_account_url)
        self.assertRedirects(response, self.home_url)
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_password_reset(self):
        """Test password reset functionality"""
        # Test GET request
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset.html')

        # Test successful password reset request
        response = self.client.post(self.password_reset_url, {
            'email': 'test@example.com'
        })
        self.assertRedirects(response, self.password_reset_done_url)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('test@example.com', mail.outbox[0].to)

    def test_password_reset_confirm(self):
        """Test password reset confirm functionality"""
        # First, create user and get valid token
        user = User.objects.create_user(username='resetuser', email='reset@example.com', password='oldpass123')
        
        # Generate token
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        reset_url = reverse('account:password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': token
        })
        
        # First get to set session
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 302)  # Should redirect to same URL with internal reset session
        
        # Follow redirect and post new password
        response = self.client.post(response.url, {
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        })
        self.assertRedirects(response, self.login_url)

        # Verify new password works
        self.assertTrue(
            self.client.login(username='resetuser', password='newpass456')
        )