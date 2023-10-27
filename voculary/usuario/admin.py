from datetime import date, timedelta

from django.contrib import admin, messages
from django.db.models import Avg, Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse

from gerenciamento_texto.models import DigitizedText
from .models import User


class UsuarioAdmin(admin.ModelAdmin):
    def data_formatada(self, obj):
        return obj.date_joined.strftime('%d/%m/%Y')
        
    data_formatada.admin_order_field = 'date_joined'
    data_formatada.short_description = 'Data de registro'

    def has_add_permission(self, request):
        return request.user.is_admin

    def has_change_permission(self, request, obj=None):
        return request.user.is_admin

    def has_delete_permission(self, request, obj=None):
        return request.user.is_admin

    def editar_usuarios_selecionados(self, request, queryset):
        if queryset.count() == 1:
            user_id = queryset.first().id
            return HttpResponseRedirect(str(user_id))
        self.message_user(request, "Por favor, selecione apenas um usuário para editar.", level=messages.ERROR)

    def visualizar_usuarios_selecionados(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Por favor, selecione apenas um usuário para visualizar.", level=messages.ERROR)
            return

        user_id = queryset.first().id
        return HttpResponseRedirect(reverse('admin:usuario_user_view', args=[user_id]))

    def delete_model(self, request, obj):
        """
        Sobrescreve o comportamento padrão da exclusão para desativar o usuário em vez de excluir.
        """
        obj.is_active = False
        obj.save()
        messages.success(request, "Usuário desativado com sucesso!")

    def delete_queryset(self, request, queryset):
        """
        Sobrescreve o comportamento padrão da exclusão em massa para desativar os usuários em vez de excluir.
        """
        queryset.update(is_active=False)
        messages.success(request, "Usuários desativados com sucesso!")

    def response_change(self, request, obj):
        if "_deactivate" in request.POST:
            self.message_user(request, "Usuário(s) desativado(s) com sucesso.", level=messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:index'))
        return super().response_change(request, obj)

    def get_actions(self, request):
        actions = super(UsuarioAdmin, self).get_actions(request)
        if not request.user.is_admin:
            if 'editar_usuarios_selecionados' in actions:
                del actions['editar_usuarios_selecionados']
        return actions

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/view/', self.admin_site.admin_view(self.visualizarUsuarioView), name='usuario_user_view'),
        ]
        return custom_urls + urls

    def visualizarUsuarioView(self, request, user_id, *args, **kwargs):
        usuario = get_object_or_404(User, id=user_id)
        context = dict(
            self.admin_site.each_context(request),
            usuario=usuario
        )

        return render(request, "admin/visualizar_usuario.html", context)


    def get_fieldsets(self, request, obj=None):
        """
        Sobrescreve campos do Admin
        """
        fieldsets = super(UsuarioAdmin, self).get_fieldsets(request, obj)

        if obj is None:
            return fieldsets

        for fieldset in fieldsets:
            fields = list(fieldset[1]['fields'])
            if 'password' in fields:
                fields.remove('password')
                fieldset[1]['fields'] = tuple(fields)
                break

        return fieldsets

    list_display = ('is_active', 'id', 'email', 'first_name', 'last_name', 'data_formatada')
    list_display_links = None
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('is_active', 'is_staff', 'is_admin')
    list_per_page = 6

    delete_model.short_description = "Deletar usuário(s) selecionado(s)"
    editar_usuarios_selecionados.short_description = "Editar usuário selecionado"
    visualizar_usuarios_selecionados.short_description = "Visualizar usuário selecionado"
    actions = [editar_usuarios_selecionados, visualizar_usuarios_selecionados]


class AdminSitePersonalizado(admin.AdminSite):
    site_header = "Painel do Administrador"

    def index(self, request, extra_context=None):
        context = extra_context or {}

        # Total de usuários
        total_usuarios = User.objects.count()

        # Total de usuários ativos
        total_usuarios_ativos = User.objects.filter(is_active=True).count()

        # Usuários que ingressaram neste mês
        inicio_mes = date.today().replace(day=1)
        if date.today().month != 12:
            final_mes = date.today().replace(month=date.today().month + 1, day=1) - timedelta(days=1)
        else:
            final_mes = date(date.today().year, 12, 31)
        usuarios_mes = User.objects.filter(date_joined__range=(inicio_mes, final_mes)).count()

        # Usuários que ingressaram nesta semana
        inicio_semana = date.today() - timedelta(days=date.today().weekday())
        final_semana = inicio_semana + timedelta(days=6)
        usuarios_semana = User.objects.filter(date_joined__range=(inicio_semana, final_semana)).count()

        context.update({
            'total_textos': str(DigitizedText.objects.count()).zfill(2),
            'tempo_medio_processamento': str(round(DigitizedText.objects.aggregate(Avg('processing_time'))['processing_time__avg'], 2)).zfill(2),
            'total_usuarios_ativos': str(total_usuarios_ativos).zfill(2),
            'usuarios_mes': str(usuarios_mes).zfill(2),
            'usuarios_semana': str(usuarios_semana).zfill(2),
        })

        idioma_mais_comum = DigitizedText.objects.values('language').annotate(total=Count('language')).order_by('-total').first()

        context['idioma_mais_comum'] = idioma_mais_comum['language'] if idioma_mais_comum else "N/A"
        context['idioma_mais_comum_count'] = str(idioma_mais_comum['total']).zfill(2) if idioma_mais_comum else '00'
            
        return super().index(request, context)

admin_site = AdminSitePersonalizado(name='admin_site')
admin_site.register(User, UsuarioAdmin)
