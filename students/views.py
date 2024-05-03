class UserActivate(generics.CrateAPIviet)
    query_set = UserProfile.objects.all()
    serializer = 
    
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserProfileRegisterSerializer

class UserProfileRegisterAPIView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token_serializer = MyTokenObtainPairSerializer().get_token(user)
        return Response(token_serializer, status=status.HTTP_201_CREATED)

