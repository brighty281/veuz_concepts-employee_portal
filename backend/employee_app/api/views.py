from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from employee_app.models import User,UserProfile
from .serializers import UserRegisterSerializer,MyTokenObtainPairSerializer,UserSerializer,UserDetailsUpdateSerializer,UserProfileSerializer,AdminUserSerializer,UserProfileSerializer
from rest_framework.generics import ListCreateAPIView

from rest_framework.exceptions import AuthenticationFailed,ParseError
from django.contrib.auth import authenticate

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, FormParser


from rest_framework.generics import RetrieveAPIView
from rest_framework.generics import UpdateAPIView
from .serializers import UserUpdateSerializer
from rest_framework import generics



class RegisterView(APIView):
    def post(self,request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors,status=status.HTTP_406_NOT_ACCEPTABLE,)  
        
        content ={'Message':'User Registered Successfully'}
        return Response(content,status=status.HTTP_201_CREATED,)
    

class LoginView(APIView):
    def post(self,request):
        try:
            email = request.data['email']
            password =request.data['password']
        
        except KeyError:
            raise ParseError('All Fields Are Required')
        
        if not User.objects.filter(email=email).exists():
            raise AuthenticationFailed('Invalid Email Address')
        
        if User.objects.filter(email=email,is_superuser=True).exists():
            raise AuthenticationFailed('please log in admin login')
        
        if not User.objects.filter(email=email,is_active=True).exists():
            raise AuthenticationFailed('You are blocked by admin ! Please contact admin')
        
        user = authenticate(username=email,password=password)
        if user is None:
            raise AuthenticationFailed('Invalid Password')
        
        refresh = RefreshToken.for_user(user)
        refresh["first_name"] = str(user.first_name)
       
        content = {
                     'refresh': str(refresh),
                     'access': str(refresh.access_token),
                     'isAdmin':user.is_superuser,
                }
        
        return Response(content,status=status.HTTP_200_OK)
    

    
class UserDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = User.objects.get(id=request.user.id)
        data = UserSerializer(user).data
        try :
            profile_pic = user.User_Profile.profile_pic
            data['profile_pic'] = request.build_absolute_uri('/')[:-1]+profile_pic.url
        except:
            profile_pic = ''
            data['profile_pic']=''
            
        content = data
        return Response(content)


    
class UserDetailsUpdate(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.get_or_create(user=request.user)[0]

        
        user_update_details_serializer = UserDetailsUpdateSerializer(
            user_profile, data=request.data, partial=True
        )
        
       
        if user_update_details_serializer.is_valid():
           
            user_update_details_serializer.save()
            return Response(user_update_details_serializer.data, status=status.HTTP_201_CREATED)
        else:
            print('error', user_update_details_serializer.errors)
            return Response(user_update_details_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
###################### ADMIN SIDE ####################

class AdminLoginView(APIView):
    def post(self,request):
        try:
            email = request.data['email']
            password =request.data['password']
        
        except KeyError:
            raise ParseError('All Fields Are Required')
        
        if not User.objects.filter(email=email).exists():
            raise AuthenticationFailed('Invalid Email Address')
        
        if User.objects.filter(email=email,is_superuser=False).exists():
            raise AuthenticationFailed('please log in employee view')
        
        
        user = authenticate(username=email,password=password)
        if user is None:
            raise AuthenticationFailed('Invalid Password')
        
        refresh = RefreshToken.for_user(user)
        refresh["first_name"] = str(user.first_name)
       
        content = {
                     'refresh': str(refresh),
                     'access': str(refresh.access_token),
                     'isAdmin':user.is_superuser,
                }
        
        return Response(content,status=status.HTTP_200_OK)



class AdminUserListCreateView(ListCreateAPIView):
    queryset = User.objects.all().order_by('-date_joined')  
    serializer_class = AdminUserSerializer


class AdminUserRetrieveView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    lookup_field = 'id'
    
class AdminUserUpdateView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    lookup_field = 'id'
    
class AdminUserDeleteView(APIView):
    def delete(self, request, id):
        try:
            user = User.objects.get(id=id)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        