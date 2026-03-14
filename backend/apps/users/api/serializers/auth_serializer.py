# apps/users/api/serializers/auth_serializer.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    # الدالة دي بتشفر البيانات جوه التوكن نفسه (عشان لو حبيت تفك شفرته في الفلاتر)
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # إضافة بيانات إضافية للتوكن
        token['username'] = user.username
        token['email'] = user.email
        return token

    # الدالة دي بتشكل الرد (Response JSON) اللي هيرجع للموبايل
    def validate(self, attrs):
        data = super().validate(attrs) # دي بتجيب الـ access والـ refresh توكن
        
        # هنضيف قاموس (Dictionary) جواه بيانات اليوزر
        data.update({
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
            }
        })
        return data