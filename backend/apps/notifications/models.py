
from django.db import models

#project imports 
from apps.users.models import CustomUser
from apps.blog.models import Comment


class Notification(models.Model):
    recipient = models.ForeignKey(CustomUser,on_delete=models.CASCADE,
                                  related_name="notifications")
    comment = models.ForeignKey(Comment,on_delete=models.CASCADE,
                                related_name="notifications")
    is_read = models.BooleanField(default=False)
    created_at =models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ["-created_at"]
        