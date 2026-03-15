# apps/users/api/serializers/auth_serializer.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # إحنا هنا مش محتاجين نغير كتير لأن السلايزر بيقرأ الـ USERNAME_FIELD أوتوماتيك
    # بس التأكيد على البيانات الإضافية في التوكن ده شغل عالي
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # بيانات إضافية مشفرة جوه التوكن
        token['email'] = user.email
        token['first_name'] = user.first_name
        return token

    def validate(self, attrs):
        # attrs هنا هتاخد الإيميل والباسورد من الريكويست
        data = super().validate(attrs)
        
        # إضافة بيانات اليوزر في الرد النهائي (JSON)
        data.update({
            'user': {
                'id': self.user.id,
                'email': self.user.email,
                'full_name': f"{self.user.first_name} {self.user.last_name}",
            }
        })
        return data