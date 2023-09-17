from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.utils import timezone

from .forms import UploadImagemForm
from .models import Imagem, TextoDigitalizado

from .utils.extrair_texto import extrair_texto

import datetime, time, os, io, requests
import base64

@login_required(login_url='/login')
def GeracaoTextoView(request):
    cache_key = f"{request.user.id}_texto_e_imagem"
    cached_data = cache.get(cache_key, {})

    texto = cached_data.get("texto", "")
    imagem_data = cached_data.get("imagem_data") 
    tempo_processamento = cached_data.get("tempo_processamento")
    idioma = cached_data.get("idioma")

    if request.method == 'POST':
        form = UploadImagemForm(request.POST, request.FILES)
        if form.is_valid():
            if 'extrair' in request.POST:
                imagem_data, texto, tempo_processamento, idioma = obter_extracao(form, request)

                cache.set(cache_key, {
                    "texto": texto, 
                    "imagem_data": imagem_data,  
                    "tempo_processamento": tempo_processamento,
                    "idioma": idioma
                }, 3600)

            elif 'salvar' in request.POST:
                imagem_model_instance = salvar(imagem_data, texto, tempo_processamento, idioma, request) 
                cache.delete(cache_key)

    else:
        cache.delete(cache_key)
        imagem_data, texto = None, None

    textos = TextoDigitalizado.objects.select_related('imagem').order_by('-data_geracao').filter(usuario=request.user, ativo=True)[:4]

    imagem_base64 = None
    if imagem_data:
        imagem_base64 = f"data:image/jpeg;base64,{base64.b64encode(imagem_data).decode('utf-8')}"

    form = UploadImagemForm()
    context = {
        'form': form,
        'texto': texto,
        'textos': textos,
        'imagem_base64': imagem_base64
    }

    return render(request, 'gerenciamento_texto/gerar_textos.html', context)


import numpy as np
def obter_extracao(form, request):
    imagem = form.instance
    imagem.usuario = request.user
    imagem_content = None
    texto = None
    idioma = None

    try:
        if form.cleaned_data['url']:
            url = form.cleaned_data['url']
            response = requests.get(url)
            if response.status_code == 200:
                imagem_content = response.content
                imagem_object = io.BytesIO(imagem_content)
                texto, idioma = extrair_texto(imagem_object)
        else:
            imagem_content = form.cleaned_data['arquivo'].read()
            texto, idioma = extrair_texto(io.BytesIO(imagem_content))

        inicio_tempo = datetime.datetime.now(tz=timezone.utc)
        fim_tempo = datetime.datetime.now(tz=timezone.utc)
        tempo_processamento = (fim_tempo - inicio_tempo).seconds

        cache.set(f"{request.user.id}_imagem", imagem_content, 3600)
        return imagem_content, texto, tempo_processamento, idioma
    except Exception as e:
        print(e)  
        messages.error(request, f'Puxa, parece que não foi possível extrair o texto. Tente novamente com outra imagem.')
        return None, None, None, None  # Certifique-se de retornar valores que correspondam ao que sua função normalmente retornaria.

def salvar(imagem, texto, tempo_processamento, idioma, request):
    time.sleep(1)
    imagem_content = cache.get(f"{request.user.id}_imagem")

    imagem = Imagem(usuario=request.user)  
    imagem.arquivo.save('nome_da_imagem.jpg', ContentFile(imagem_content))
    imagem.save()
    
    texto_digitalizado = TextoDigitalizado(
        nome=os.path.basename(imagem.arquivo.path),
        texto=texto,
        tempo_processamento=tempo_processamento,
        usuario=request.user,
        imagem=imagem,
        idioma=idioma,
        ativo=True,
    )
    texto_digitalizado.save()
    messages.success(request, f'Imagem salva com sucesso! Você pode visualizá-la indo em "Meus textos".')


@login_required(login_url='/login')
def MeusTextosView(request):

    textos = TextoDigitalizado.objects.select_related('imagem').filter(usuario=request.user, ativo=True)

    if len(textos) == 0:
        mensagem = 'Puxa! Parece que você ainda não salvou nenhum texto.'
        return render(request, 'partials/_aviso.html', {'mensagem': mensagem})
    else:
        paginator = Paginator(textos, 5)
        page = request.GET.get('page')
        paginados = paginator.get_page(page)

        return render(request, 'gerenciamento_texto/meus_textos.html', {'paginados': paginados})
        

from django.http import JsonResponse

def obter_info_texto(request, id_imagem):
    texto = TextoDigitalizado.objects.get(imagem__id_imagem=id_imagem)
    
    data = {
        'nome': texto.nome,
        'data_geracao': texto.data_geracao.strftime('%d/%m/%Y'),
        'imagem_url': texto.imagem.arquivo.url,
        'texto': texto.texto
    }
    
    return JsonResponse(data)

from django.views.decorators.http import require_POST

@require_POST
def desativar_texto(request, texto_id):
    messages.success(request, 'Texto excluído com sucesso!')
    try:
        texto = TextoDigitalizado.objects.get(id=texto_id)
        imagem = TextoDigitalizado.objects.get(id=texto_id)
        texto.ativo, imagem.ativo = False, False
        texto.save()
        imagem.save()
        return JsonResponse({"success": True, "message": "Texto excluído com sucesso!"})
    except:
        pass


