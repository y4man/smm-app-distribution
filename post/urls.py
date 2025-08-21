from django.urls import path
from . import views


urlpatterns = [

    # ✅ Lists and Create all post attributes
    path('', views.PostAttributeListCreateView.as_view(), name='post-attribute-create'),

    # ✅ List all the post according to attribute type
    path('<str:attribute_type>', views.PostAttributeByTypeView.as_view(), name='post-attribute-by-type'),

    # ✅ Update a single post attribute
    path('update/<int:pk>', views.PostAttributeUpdateView.as_view(), name='post-attribute-update'),
]