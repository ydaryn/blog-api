from rest_framework import serializers
#project imports
from apps.notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
      class Meta:
          model = Notification
          fields = ["id", "comment", "is_read", "created_at"]