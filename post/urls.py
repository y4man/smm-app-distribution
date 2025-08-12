from django.urls import path
from . import views


urlpatterns = [

    # ✅ Lists and Create all post attributes
    path('attributes', views.PostAttributeListCreateView.as_view(), name='post-attribute-create'),

    # ✅ List all the post according to attribute type
    path('attributes/<str:attribute_type>', views.PostAttributeByTypeView.as_view(), name='post-attribute-by-type'),

    # ✅ Update a single post attribute
    path('attributes/update/<int:pk>', views.PostAttributeUpdateView.as_view(), name='post-attribute-update'),
]