from rest_framework import ModelSerializer
from .models import Amenity

class AmenitySerializer(ModelSerializer):

    class Meta:
        model = Amenity
        fields = "__all__"