from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.contrib.auth.decorators import login_required
from .models import Profile
from db_queries import (update_billing_email,)
from user.forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from orders.models import Invoice, cart, cart_records, customerOrderHistory, OrderAmount
import requests
from accounts import views

def logout(request):
    return redirect(to='')

# custom 404 view



def custom_404(request, exception):
    return render(request, 'users/404.html', status=404)


class RegisterView(View):
    form_class = RegisterForm
    template_name = 'users/register.html'

    def get(self, request):
        print("GET request - creating new form")
        form = self.form_class()
        print("Form fields:", form.fields.keys())
        user=request.session['user']
        return render(request, self.template_name, {'form': form,'user':user})

    def post(self, request):
        print("POST request received")
        form = self.form_class(request.POST)
        print("Form is valid?", form.is_valid())
        
        if form.is_valid():
            user_details = request.session.get('user', {})
            
            if not user_details:
                return render(request, self.template_name, {
                    'form': form,
                    'error': "Missing session data. Please complete the previous registration steps."
                })

           
                
            role = form.cleaned_data['role']
            group_name = role.lower()  # Ensure lowercase to match your choices
                
            group, created = Group.objects.get_or_create(name=group_name)
                
            user_details['role']=role
            request.session['user']=user_details
            print("user ",user_details)
            return render(request,'accounts/index.html',{'user':user_details})
                
           

        return render(request, self.template_name, {'form': form})

# Class based view that extends from the built in login view to add a remember me functionality


# class CustomLoginView(LoginView, SuccessMessageMixin):
#     form_class = LoginForm

#     def form_valid(self, form):
#         remember_me = form.cleaned_data.get('remember_me')

#         if not remember_me:
#             # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
#             self.request.session.set_expiry(0)

#             # Set session as modified to force data updates/cookie to be saved.
#             self.request.session.modified = True

#         # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
#         return super(CustomLoginView, self).form_valid(form)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('index')


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('login')


def profile(request):
    
    user=request.session['user']
    id=user['user_id']
    api_endpoint = 'http://127.0.0.1:5000/stemuserprofiles'
    url = f"{api_endpoint}/{id}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP errors

        user = response.json()
    except request.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    profile_info = user

    #if request.method == 'POST':
        #user_form = UpdateUserForm(request.POST, instance=request.user)
        #profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        #if user_form.is_valid() and profile_form.is_valid():
            #user_form.save()
            #profile_form.save()
            #messages.success(request, 'Your profile is updated successfully')
            #return redirect(to='users-profile')
    #else:
        #user_form = UpdateUserForm(instance=request.user)
        #profile_form = UpdateProfileForm(instance=request.user.profile)

        # update order management
    customer_name = user
    username=customer_name['first_name']+" "+customer_name['last_name']
    email=customer_name['email']
   

    api_endpoint = 'http://127.0.0.1:5000/users_profiles'
    url = f"{api_endpoint}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP errors

        users = response.json()
        print("all users ", users)
    except request.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    if 'admin' in user:
        return render(request, 'users/admin_profile.html', {'users': users})
    else:
        return render(request, 'users/profile.html', {'profile': profile_info, 'user': customer_name})



def view_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    # You can fetch additional information related to the user if needed
    return render(request, 'users/view_user.html', {'user': user})
