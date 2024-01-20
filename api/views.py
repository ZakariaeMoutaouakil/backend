from datetime import datetime, timedelta

import jwt
import pytz
import validators
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import driver, secret


def validate(email, password=None):
    return validators.email(email)


def execute_query(query_string):
    records, summary, keys = driver.execute_query(
        query_string,
        database_="neo4j",
    )
    return [record.data() for record in records]


@api_view(['GET'])
def read(request):
    node_filter, node_property, node_result = request.GET.dict().values()
    result = execute_query(f"MATCH (n:Data{{{node_filter}:\"{node_property}\"}}) RETURN DISTINCT n.{node_result}")
    return JsonResponse([record[f"n.{node_result}"] for record in result], safe=False)


@api_view(['GET'])
def composantes(request):
    result = execute_query(
        """
        match (n:Data)
        return distinct n.type, n.subject
        """
    )
    data = {}
    for subject in result:
        data[subject['n.type']] = []
    for subject in result:
        data[subject['n.type']].append(subject["n.subject"])
    return JsonResponse(data)


@api_view(['POST'])
def login(request):
    email = request.data["user"]["email"]
    password = request.data["user"]["password"]
    result = execute_query(
        f"""
        match (n:User)
        where n.email = "{email}" and n.password = "{password}"
        return count(*) as count
        """
    )[0]["count"]
    if result > 0:
        return JsonResponse(
            {"access_token": jwt.encode(
                {"email": email,
                 "exp": datetime.now(tz=pytz.timezone("Europe/Paris")) + timedelta(hours=10)},
                secret,
                algorithm="HS256"
            )})
    else:
        content = {'message': 'Veuillez entrer des coordonnées valides.'}
        return Response(content, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def signup(request):
    name = request.data["user"]["name"]
    email = request.data["user"]["email"]
    password = request.data["user"]["password"]

    if not validate(email, password):
        content = {'message': 'Veuillez entrer des coordonnées valides.'}
        return Response(content, status=status.HTTP_403_FORBIDDEN)

    summary = driver.execute_query(
        "MERGE (:User {name: $name, email: $email, password: $password})",
        name=name,
        email=email,
        password=password,
        database_="neo4j",
    ).summary
    print("Created {nodes_created} nodes in {time} ms.".format(
        nodes_created=summary.counters.nodes_created,
        time=summary.result_available_after
    ))
    content = {'message': 'Vous êtes bien enregistré.'}
    return Response(content, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def subscribe(request):
    encoded_jwt = request.data["access_token"]
    decoded_jwt = jwt.decode(encoded_jwt, secret, algorithms=["HS256"])
    email = decoded_jwt["email"]
    course = request.data["course"]
    condition = execute_query(
        f"""
            MATCH (p:User {{email:"{email}"}}), (q:Data{{course:"{course}"}})
            RETURN exists((p)-[:TAKES]-(q)) AS result
            """
    )[0]["result"]
    if condition:
        driver.execute_query(
            """
            MATCH (p:User {email: $email})-[r:TAKES]->(q:Data{course: $course})
            DELETE r
            """,
            email=email,
            course=course,
            database_="neo4j",
        )
        return Response(status=status.HTTP_201_CREATED)
    else:
        driver.execute_query(
            """
            MATCH (p:User {email: $email}), (q:Data{course: $course})
            MERGE (p)-[:TAKES]->(q)
            RETURN p,q
            """,
            email=email,
            course=course,
            database_="neo4j",
        )
        return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
def cours(request):
    curriculum = request.query_params.get('parcours')
    encoded_jwt = request.query_params.get("access_token")
    decoded_jwt = jwt.decode(encoded_jwt, secret, algorithms=["HS256"])
    email = decoded_jwt["email"]
    result = execute_query(
        f"""
        MATCH (n:Data)
        WHERE n.curriculum="{curriculum}"
        RETURN n.professor as prof, n.course as title, n.description as description, 
        exists((:User{{email:"{email}"}})-[:TAKES]->(n)) as subscribe
        """
    )
    return JsonResponse(result, safe=False)
