import re
from datetime import datetime

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import redirect, render

from usuario.forms import (CadastroForms, LoginForms, PerfilForms,
                           PerfilSenhaForms)
from usuario.models import User
from .utils.enviar_email_reativacao import enviar_email_reativacao


def cadastro_view(request):
    """
    Permite que um novo usuário se cadastre no sistema.
    """

    if request.user.is_authenticated:
        return redirect('gerar-textos')

    form = CadastroForms(request.POST or None)

    if form.is_valid():
        dados_do_formulario = form.cleaned_data
        email = dados_do_formulario['email']

        usuario = User.objects.filter(email=email).first()

        if usuario:
            if not usuario.is_active:
                messages.info(request, 'Puxa, parece que esse e-mail já existe e foi desativado. Caso queira recuperá-lo, acesse a página de Login.')
                return redirect('login')

            messages.error(request, 'Ops, parece que este e-mail já existe! Tente novamente.')
            return redirect('cadastro')

        # Utilizando a criação de usuário diretamente com os dados do form
        usuario = User.objects.create_user(
            first_name=dados_do_formulario['primeiro_nome'],
            last_name=dados_do_formulario['ultimo_nome'],
            email=email,
            password=dados_do_formulario['senha_1']
        )

        messages.success(request, 'Eba! O cadastro foi realizado com sucesso.')
        return redirect('login')

    contexto = {
        'form': form,
        'mostra_cabecalho_usuario': bool(re.match(r'^/cadastro/*?$', request.path))
    }

    return render(request, 'usuario/cadastro.html', contexto)

def login_view(request):
    """
    Faz login do usuário no sistema, identificando se ele realmente possui uma conta 
    ou se é necessario reativá-la. 
    """

    # Caso usuário já esteja autenticado, redireciona
    if request.user.is_authenticated:
        return redirect('gerar-textos')

    form = LoginForms(request.POST or None)
    modal_confirmacao_email = False

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        senha = form.cleaned_data['senha']
        modeloUsuario = auth.get_user_model()
        usuario = modeloUsuario.objects.filter(email=email).first()

        if usuario and usuario.check_password(senha):
            # Se o usuário está inativo, envia o e-mail de reativação
            if not usuario.is_active:
                modal_confirmacao_email = True
                enviar_email_reativacao(usuario)
                messages.info(request, 'Puxa, parece que esse e-mail já existe e foi desativado. Caso queira reativá-lo, te enviamos um e-mail!')
                return redirect('login')
            else:
                usuario.ultimo_login = datetime.now()
                usuario.save()
                auth.login(request, usuario)
                messages.success(request, f'Olá, {usuario.first_name}! O login foi realizado com sucesso.')
                return redirect('gerar-textos')
        
        # Se chegou até aqui, ou o usuário não existe, ou a senha está incorreta
        messages.error(request, 'Oops! Usuário ou senha incorretos, tente novamente.')
        return redirect('login')

    contexto = {
        'form': form,
        'mostra_cabecalho_usuario': bool(re.match(r'^/login/*?$', request.path)),
        'modal_confirmacao_email': modal_confirmacao_email
    }

    return render(request, 'usuario/login.html', contexto)

@login_required(login_url='/login')
def perfil_view(request):
    """
    Permite que o usuário edite seu perfil, altere sua senha ou exclua sua conta.
    """
    usuario_atual = User.objects.get(id=request.user.id)
    form_dados_gerais = PerfilForms(request.POST or None, instance=usuario_atual)
    form_alterar_senha = PerfilSenhaForms(request.POST or None)

    if request.method == "POST":
        tipo_de_formulario = request.POST.get('tipo-form')

        if tipo_de_formulario == 'info_geral' and form_dados_gerais.is_valid():
            form_dados_gerais.save()
            messages.success(request, 'Dados atualizados com sucesso.')

        elif tipo_de_formulario == 'senha':
            if form_alterar_senha.is_valid():
                if usuario_atual.check_password(form_alterar_senha.cleaned_data['senha_antiga']):
                    usuario_atual.set_password(form_alterar_senha.cleaned_data['senha_nova'])
                    usuario_atual.save()
                    messages.success(request, 'Senha atualizada com sucesso.')
                else:
                    messages.error(request, 'Senha antiga incorreta.')
            else:
                for erro in form_alterar_senha.non_field_errors():
                    messages.error(request, erro)

        elif tipo_de_formulario == 'excluir':
            usuario_atual.is_active = False
            usuario_atual.save()
            messages.success(request, 'Conta excluída com sucesso.')
            auth.logout(request)
            return redirect('/home')

    contexto = {
        'form_dados_gerais': form_dados_gerais,
        'form_alterar_senha': form_alterar_senha
    }

    return render(request, 'usuario/perfil.html', contexto)

def reativar_conta_view(request, user_id, token):
    """
    Realiza a reativação da conta de um usuário que antes a desativou.
    """
    try:
        usuario = User.objects.get(pk=user_id)
    except usuario.DoesNotExist:
        usuario = None
    
    if usuario and not usuario.is_active and PasswordResetTokenGenerator().check_token(usuario, token):
        usuario.is_active = True
        usuario.save()

    return render(request, 'usuario/reativar_conta.html')

@login_required(login_url='/login')
def logout_view(request):
    """
    Faz logout do usuário atualmente autenticado e redireciona para a página inicial.
    """
    messages.success(request, 'Até mais! O logout foi efetuado com sucesso.')
    auth.logout(request)

    return redirect('/home')