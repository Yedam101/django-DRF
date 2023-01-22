from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.exceptions import NotFound, NotAuthenticated, ParseError

from categories.models import Category
from .models import Amenity, Room
from .serializers import AmenitySerializer, RoomListSerializer, RoomDetailSerializer


class Rooms(APIView):

    def get(self, request):
        all_rooms = Room.objects.all()
        serializer = RoomListSerializer(all_rooms, many=True)
        return Response(RoomListSerializer(serializer).data)


    def post(self, request):
        if request.user.is_authenticated: # 로그인한 유저인 경우
            serializer = RoomDetailSerializer(data=request.data)
            if serializer.is_valid():
                category_pk = request.data.get("category")
                if not category_pk:
                    raise ParseError
                try:
                    category = Category.objects.get(pk=category_pk)
                except Category.DoesNotExist:
                    raise ParseError
                new_room = serializer.save(owner=request.user, category)
                return Response(RoomDetailSerializer(new_room).data)
            else:
                return Response(serializer.errors)
        else:
            raise NotAuthenticated



class RoomDetail(APIView):

    def get_object(self, pk):
        try:
            return Room.objects.get(pk)
        except Room.DoesNotExist:
            raise NotFound

    
    def get(self, request, pk):
        serializer = RoomDetailSerializer(self.get_object(pk))
        return Response(serializer.data)


    def put(self, request, pk):
        if request.user.is_authenticated():
            room = self.get_object(pk)
            serializer = RoomDetailSerializer(room, data=request.data, partial=True)
            if serializer.is_valid():
                updated_room = serializer.save()
                return Response(RoomDetailSerializer(updated_room).data)
            else:
                return Response(serializer.errors)
        else:
            raise NotAuthenticated



    def delete(self, request, pk):
        pass




class Amenities(APIView):

    def get(self, request):
        all_amenities = Amenity.objects.all()
        serializer = AmenitySerializer(all_amenities, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = AmenitySerializer(data=request.data)
        if serializer.is_valid():
            amenity = serializer.save()
            return Response(AmenitySerializer(amenity).data)
        else:
            return Response(serializer.errors)
            


class AmenityDetail(APIView):

    def get_object(self, pk):
        try:
            return Amenity.objects.get(pk=pk)
        except Amenity.DoesNotExist:
            raise NotFound
        

    def get(self, request, pk):
        amenity = self.get_object(pk)
        serializer = AmenitySerializer(amenity)
        return Response(serializer.data)


    def put(self, request, pk):
        amenity = self.get_object(pk)
        serializer = AmenitySerializer(amenity, data=request.data, partial=True)
        if serializer.is_valid():
            updated_amenity  = serializer.save()
            return Response(AmenitySerializer(updated_amenity).data)
        else:
            return Response(serializer.errors)


    def delete(self, request, pk):
        amenity = self.get_object(pk)
        amenity.delete()
        return Response(HTTP_204_NO_CONTENT)