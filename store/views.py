from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response
from store.filters import ProductFilter
from store.pagination import DefaultPaginatiopn
from store.permission import IsAdminOrReadOnly
from .models import Cart, CartItem, Customer, Product, Collection, OrderItem, Review
from .serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer, CustomerSerializer, ProductSerializer, CollectionSerailizer, ReviewSerializer, UpdateCartItemSerializer
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser



class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = DefaultPaginatiopn
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'last_update']
    permission_classes = [IsAdminOrReadOnly]


    def get_serializer_context(self):
        return {'request':self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id = kwargs['pk']).count()>0:
            return Response({'error':'Product cannot be deleted cause it is associated with order.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(products_count = Count('products')).all()
    serializer_class = CollectionSerailizer
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_context(self):
        return {'reqeust':self.request}
    
    def destroy(self, request, *args, **kwargs):
        if Collection.objects.filter(products=kwargs['pk']).count() > 0:
            return Response({'error': 'Product cannot be deleted cause it is associated with order.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)



class ReviewViewSet(ModelViewSet):

    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id = self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id':self.kwargs['product_pk']}


class CartViewSet(CreateModelMixin,
                RetrieveModelMixin,
                DestroyModelMixin,
                GenericViewSet,
                ListModelMixin
                   ):
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer

class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id' : self.kwargs['cart_pk']}


    def get_queryset(self):
        return CartItem.objects.filter(cart_id = self.kwargs['cart_pk']).select_related('product')


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail = False, methods = ['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        (customer, created) = Customer.objects.get_or_create(user_id = request.user.id)

        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data = request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True)
    def history(self, request, pk):
        return Response("Okay")

    # def get_permissions(self):
    #     if self.request.method == 'GET':
    #         return [AllowAny()]
    #     return [IsAdminUser()]
