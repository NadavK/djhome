from rest_framework.permissions import IsAdminUser


class IsAdminOrIsSelf(IsAdminUser):
    """
    Allow access to admin users or the user himself.
    """
    def has_object_permission(self, request, view, obj):



        #permission is never  called!!!!!
        return False



        if request.user and request.user.is_staff:
            print('has_object_permission True')
            return True
        elif (request.user and type(obj) == type(request.user) and
              obj == request.user):
            return True
        print('has_object_permission False')
        return False
