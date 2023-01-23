from django.conf import settings
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.exceptions import NotFound, NotAuthenticated, ParseError, PermissionDenied

from categories.models import Category
from .models import Amenity, Room
from .serializers import AmenitySerializer, RoomListSerializer, RoomDetailSerializer
from reviews.serializers import ReviewSerializer
from medias.seializers import PhotoSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class Rooms(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        all_rooms = Room.objects.all()
        serializer = RoomListSerializer(all_rooms, many=True, context={"request":request})
        return Response(serializer.data)

    # permission_classes = [IsAuthenticatedOrReadOnly] 사용 전
    ''' 
    def post(self, request):
        if request.user.is_authenticated: # 로그인한 유저인 경우
            serializer = RoomDetailSerializer(data=request.data)
            if serializer.is_valid():
                category_pk = request.data.get("category") # 유저가 보낸 데이터로 카테고리의 id 찾음
                if not category_pk: # 유저가 카테고리 안 보냈으면
                    raise ParseError("Category is required.") # 에러 반환 그냥 ParseError 라고만 써도 되지만 구체적 원인을 써줌.
                try:
                    category = Category.objects.get(pk=category_pk) # 카테고리 보냈으면 DB에서 유저가 보낸 카테고리에 맞는 카테고리 꺼내옴
                    if category.kind == Category.CategoryKindChoices.EXPERIENCES: # 그런데 그 카테고리 id가 EXPERIENCES의 카테고리이면
                        raise ParseError("The category kind should be 'rooms'") # 에러 반환
                except Category.DoesNotExist: # DB에 카테고리가 없다면
                    raise ParseError("Category not found") # 에러 반환
                try: # 중간에 실패하면 new_room.delete()하는 대신 transaction으로 과정 묶어줌
                    with transaction.atomic():
                        new_room = serializer.save(owner=request.user, category=category)
                        amenities = request.data.get("amenities")
                        for amenity_pk in amenities:
                            amenity = Amenity.objects.get(pk=amenity_pk)
                            new_room.amenities.add(amenity)
                        return Response(RoomDetailSerializer(new_room).data)
                except Exception:
                    raise ParseError("Amenity not found")
            else: # serializer validation 통과 못 함
                return Response(serializer.errors) # 에러 반환 
        else: # 로그인 안 된 유저
            raise NotAuthenticated
    '''

    # permission_classes = [IsAuthenticatedOrReadOnly] 사용 후
    def post(self, request):
        serializer = RoomDetailSerializer(data=request.data)
        if serializer.is_valid():
            category_pk = request.data.get("category")
            if not category_pk:
                raise ParseError("Category is required.")
            try:
                category = Category.objects.get(pk=category_pk)
                if category.kind == Category.CategoryKindChoices.EXPERIENCES:
                    raise ParseError("The category kind should be 'rooms'")
            except Category.DoesNotExist:
                raise ParseError("Category not found")
            try:
                with transaction.atomic():
                    room = serializer.save(
                        owner=request.user,
                        category=category,
                    )
                    amenities = request.data.get("amenities")
                    for amenity_pk in amenities:
                        amenity = Amenity.objects.get(pk=amenity_pk)
                        room.amenities.add(amenity)
                    serializer = RoomDetailSerializer(room)
                    return Response(serializer.data)
            except Exception:
                raise ParseError("Amenity not found")
        else:
            return Response(serializer.errors)


  

class RoomDetail(APIView):
    
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Room.objects.get(pk)
        except Room.DoesNotExist:
            raise NotFound

    
    def get(self, request, pk):
        serializer = RoomDetailSerializer(self.get_object(pk), context={"request":request})
        return Response(serializer.data)


    def put(self, request, pk):
        room = self.get_object(pk)
        ''' 
        if not request.user.is_authenticated: # 로그인 되었는지 체크
            raise NotAuthenticated       
        '''
        if room.owner != request.user: # 현 유저가 방의 오너인지 체크
            raise PermissionDenied
        serializer = RoomDetailSerializer(room, data=request.data, partial=True)
        if serializer.is_valid():
            updated_room = serializer.save()
            return Response(RoomDetailSerializer(updated_room).data)
        else:
            return Response(serializer.errors)




    def delete(self, request, pk):
        room = self.get_object(pk)
        '''
        if request.user.is_authenticated() : # 로그인 되었는지 체크
            raise NotAuthenticated
        '''
        if room.owner != request.user: # 현 유저가 방의 오너인지 체크
            raise PermissionDenied
        room.delete()
        return Response(HTTP_204_NO_CONTENT)




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



class RoomReviews(APIView):

    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise NotFound

    
    def get(self, request, pk):
        try: # pagenation
            page = request.query_params.get("page", 1) # 쿼리 데이터(page) 가져오기, 디폴트는 1
            page = int(page)
        except ValueError: # 쿼리 값이 int로 변환되지 않는 값이라면 1로
            page = 1
        page_size = settings.PAGE_SIZE # settings.py에 설정되어있는 3, 세개의 데이터를 한 페이지에
        start = (page - 1) * page_size
        end = start + page_size
        room = self.get_object(pk)
        serializer = ReviewSerializer(room.reviews.all()[start:end], many=True)
        return Response(serializer.data)



class RoomPhotos(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise NotFound

    def post(self, request, pk):
        room = self.get_object(pk)
        '''
        if not request.user.is_authenticated:
            raise NotAuthenticated
        '''
        if request.user != room.owner:
            raise PermissionDenied
        serializer = PhotoSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(room=room)
            serializer = PhotoSerializer(photo)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


