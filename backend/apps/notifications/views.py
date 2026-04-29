
#third-party imports
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK


#project imports
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.abstract.pagination import DefaultPagination

class NotificationViewSet(ViewSet):
    
    permission_classes = [IsAuthenticated]

    # GET /api/notifications/count/
    
    @action(methods=["GET"],detail=False,url_path="count")
    def count(self,request):
        unread = Notification.objects.filter(recipient = request.user,
                                             is_read = False).count()
        return Response({"unread_count":unread})
    

    # GET /api/notifications/ 
    def list(self,request):
        qs = Notification.objects.filter(recipient = request.user)
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(qs,request)
        seralizer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(seralizer.data)
    

    @action(methods=["POST"],detail=False, url_path="read")

    def mark_read(self,request):
        Notification.objects.filter(recipient = request.user,
                                    is_read=False).update(is_read=True)
        return Response({"status":"ok"})
    