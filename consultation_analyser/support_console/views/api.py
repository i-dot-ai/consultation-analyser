from rest_framework.decorators import api_view
from rest_framework.response import Response

from consultation_analyser.support_console import serializers

# TODO - add auth!!


@api_view()
def hello_world(request):
    return Response({"message": "Hello world!"})


@api_view(["POST"])
def upload_json_data(request):
    data = serializers.ExampleSerializer(data=request.data)
    print("hi, here is some data.....")
    print(data)
    # TODO - this is where we would upload the data
    # TODO - add some validation
    return Response({"message": "Thanks for your data!"})
