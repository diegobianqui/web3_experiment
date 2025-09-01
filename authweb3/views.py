import json, secrets
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from web3 import Web3
from eth_account.messages import encode_defunct

def index(request):
    return render(request, "index.html")

@csrf_exempt
def get_nonce(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body or "{}")
    address = (data.get("address") or "").lower()
    if not address:
        return JsonResponse({"error": "Missing address"}, status=400)

    # crear/obtener usuario (username = address)
    user, _ = User.objects.get_or_create(username=address)
    profile = user.userprofile
    profile.nonce = secrets.token_hex(16)
    profile.save()

    return JsonResponse({"nonce": profile.nonce})

@csrf_exempt
def verify_signature(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body or "{}")
    address = (data.get("address") or "").lower()
    signature = data.get("signature")

    if not address or not signature:
        return JsonResponse({"success": False, "error": "Missing address/signature"}, status=400)

    try:
        user = User.objects.get(username=address)
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found"}, status=404)

    profile = user.userprofile
    message_text = f"Login nonce: {profile.nonce}"
    signable = encode_defunct(text=message_text)

    w3 = Web3()
    try:
        recovered = w3.eth.account.recover_message(signable, signature=signature).lower()
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Recover failed: {e}"}, status=400)

    if recovered == address:
        # rotar nonce + crear sesión
        profile.nonce = secrets.token_hex(16)
        profile.save()

        login(request, user)  # sesión de Django
        return JsonResponse({"success": True, "address": address})
    else:
        return JsonResponse({"success": False, "error": "Invalid signature"}, status=401)

@login_required
def dashboard(request):
    return JsonResponse({
        "message": f"Hola {request.user.username}, estás autenticado con MetaMask."
    })

def logout_view(request):
    logout(request)
    return redirect("home")
