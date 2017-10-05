import json
from rest_framework import generics

from django.views.generic import TemplateView, CreateView, UpdateView, FormView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404

from odin.common.mixins import CallServiceMixin, ReadableFormErrorsMixin
from odin.common.utils import transfer_POST_data_to_dict
from odin.management.permissions import DashboardManagementPermission
from odin.education.models import Material, Task
from odin.grading.services import start_grader_communication

from .mixins import CompetitionViewMixin, CreateSolutionApiMixin
from .permissions import (
    IsParticipantOrJudgeInCompetitionPermission,
    IsJudgeInCompetitionPermisssion,
    IsParticipantInCompetitionApiPerimission,
    IsParticipantInCompetitionPermission,
    IsParticipantOrJudgeInCompetitionApiPermission
)
from .models import Competition, CompetitionMaterial, CompetitionTask, Solution
from .forms import (
    CompetitionMaterialFromExistingForm,
    CompetitionMaterialModelForm,
    CompetitionTaskModelForm,
    CompetitionTaskFromExistingForm
)
from .services import (
    create_competition_material,
    create_competition_task,
    create_competition_test,
    create_gradable_solution,
    create_non_gradable_solution
)
from .serializers import CompetitionSolutionSerializer, CompetitionSerializer


class CompetitionDetailView(LoginRequiredMixin,
                            CompetitionViewMixin,
                            IsParticipantOrJudgeInCompetitionPermission,
                            TemplateView):
    template_name = 'competitions/competition_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_judge_in_competition = self.competition.judges.filter(email=self.request.user.email).exists()
        user_participant_in_competition = self.competition.participants.filter(email=self.request.user.email).exists()
        competition_data = CompetitionSerializer(self.competition).data

        context['is_user_judge_in_competition'] = user_judge_in_competition
        context['user_participant_in_competition'] = user_participant_in_competition
        context['competition_data'] = json.dumps(competition_data)

        return context


class CreateCompetitionView(DashboardManagementPermission,
                            CreateView):
    template_name = 'competitions/create_competition.html'
    model = Competition
    fields = ['name', 'start_date', 'end_date', 'slug_url']

    def get_success_url(self):
        return reverse_lazy('competitions:competition-detail',
                            kwargs={
                                'competition_slug': self.object.slug_url
                            })


class EditCompetitionView(LoginRequiredMixin,
                          CompetitionViewMixin,
                          IsJudgeInCompetitionPermisssion,
                          UpdateView):
    template_name = 'competitions/create_competition.html'

    model = Competition
    slug_field = 'slug_url'
    slug_url_kwarg = 'competition_slug'
    fields = ['name', 'start_date', 'end_date', 'slug_url']

    def get_success_url(self):
        return reverse_lazy('competitions:competition-detail',
                            kwargs={
                                'competition_slug': self.competition.slug_url
                            })


class CreateCompetitionMaterialFromExistingView(LoginRequiredMixin,
                                                CompetitionViewMixin,
                                                IsJudgeInCompetitionPermisssion,
                                                CallServiceMixin,
                                                ReadableFormErrorsMixin,
                                                FormView):
    template_name = 'competitions/existing_competition_material_list.html'
    form_class = CompetitionMaterialFromExistingForm

    def get_service(self):
        return create_competition_material

    def get_success_url(self):
        return reverse_lazy('competitions:competition-detail',
                            kwargs={
                                'competition_slug': self.competition.slug_url
                            })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['material_list'] = Material.objects.all()

        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()

        data = transfer_POST_data_to_dict(self.request.POST)
        data['competition'] = self.competition.id
        form_kwargs['data'] = data

        return form_kwargs

    def form_valid(self, form):
        data = {}
        data['existing_material'] = form.cleaned_data.get('material')
        data['competition'] = form.cleaned_data.get('competition')

        self.call_service(service_kwargs=data)

        return super().form_valid(form)


class CreateNewCompetitionMaterialView(LoginRequiredMixin,
                                       CompetitionViewMixin,
                                       IsJudgeInCompetitionPermisssion,
                                       CallServiceMixin,
                                       ReadableFormErrorsMixin,
                                       FormView):
    template_name = 'competitions/add_new_material.html'
    form_class = CompetitionMaterialModelForm

    def get_service(self):
        return create_competition_material

    def get_success_url(self):
        return reverse_lazy('competitions:competition-detail',
                            kwargs={
                                'competition_slug': self.competition.slug_url
                            })

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()

        data = transfer_POST_data_to_dict(self.request.POST)
        data['competition'] = self.competition.id

        form_kwargs['data'] = data

        return form_kwargs

    def form_valid(self, form):
        self.call_service(service_kwargs=form.cleaned_data)

        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class EditCompetitionMaterialView(LoginRequiredMixin,
                                  CompetitionViewMixin,
                                  IsJudgeInCompetitionPermisssion,
                                  ReadableFormErrorsMixin,
                                  UpdateView):
    model = CompetitionMaterial
    fields = ['identifier', 'url', 'content']
    pk_url_kwarg = 'material_id'
    template_name = 'competitions/edit_competition_material.html'

    def get_success_url(self):
        return reverse_lazy('competitions:competition-detail',
                            kwargs={
                                'competition_slug': self.object.slug_url
                            })


class CreateNewCompetitionTaskView(LoginRequiredMixin,
                                   CompetitionViewMixin,
                                   IsJudgeInCompetitionPermisssion,
                                   ReadableFormErrorsMixin,
                                   CallServiceMixin,
                                   FormView):
    template_name = 'education/add_task.html'
    form_class = CompetitionTaskModelForm

    def get_success_url(self):
        return reverse_lazy('competitions:competition-detail',
                            kwargs={
                                'competition_slug': self.competition.slug_url
                            })

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()

        if self.request.method in ['POST', 'PUT']:
            data = transfer_POST_data_to_dict(self.request.POST)

            data['competition'] = self.competition.id
            form_kwargs['data'] = data

        return form_kwargs

    def form_valid(self, form):
        create_competition_task_kwargs = {
            'name': form.cleaned_data.get('name'),
            'description': form.cleaned_data.get('description'),
            'gradable': form.cleaned_data.get('gradable'),
            'competition': form.cleaned_data.get('competition')
        }

        task = self.call_service(service=create_competition_task, service_kwargs=create_competition_task_kwargs)

        if task.gradable:
            create_test_kwargs = {
                'task': task,
                'language': form.cleaned_data.get('language'),
                'code': form.cleaned_data.get('code') if form.cleaned_data.get('code') != '' else None,
                'file': form.cleaned_data.get('file')
            }

            self.call_service(service=create_competition_test, service_kwargs=create_test_kwargs)

        return super().form_valid(form)


class CreateCompetitionTaskFromExistingView(LoginRequiredMixin,
                                            CompetitionViewMixin,
                                            IsJudgeInCompetitionPermisssion,
                                            ReadableFormErrorsMixin,
                                            CallServiceMixin,
                                            FormView):
    template_name = 'competitions/existing_task_list.html'
    form_class = CompetitionTaskFromExistingForm

    def get_service(self):
        return create_competition_task

    def get_success_url(self):
        return reverse_lazy('competitions:competition-detail',
                            kwargs={
                                'competition_slug': self.competition.slug_url
                            })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_list'] = Task.objects.all()

        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()

        if self.request.method in ('POST', 'PUT'):
            data = transfer_POST_data_to_dict(self.request.POST)
            data['competition'] = self.competition.id
            form_kwargs['data'] = data

        return form_kwargs

    def form_valid(self, form):
        create_competition_task_kwargs = {
            'existing_task': form.cleaned_data.get('task'),
            'competition': form.cleaned_data.get('competition')
        }

        self.call_service(service_kwargs=create_competition_task_kwargs)

        return super().form_valid(form)


class EditCompetitionTaskView(LoginRequiredMixin,
                              CompetitionViewMixin,
                              IsJudgeInCompetitionPermisssion,
                              ReadableFormErrorsMixin,
                              UpdateView):
    model = CompetitionTask
    fields = ['name', 'description', 'gradable']
    pk_url_kwarg = 'task_id'
    template_name = 'competitions/edit_competition_task.html'

    def get_success_url(self):
        return reverse_lazy('competitions:competition-detail',
                            kwargs={
                                'competition_slug': self.object.slug_url
                            })


class CreateGradableSolutionApiView(LoginRequiredMixin,
                                    CompetitionViewMixin,
                                    CreateSolutionApiMixin,
                                    CallServiceMixin,
                                    generics.CreateAPIView):
    serializer_class = CompetitionSolutionSerializer
    permission_classes = (IsParticipantInCompetitionApiPerimission, )

    def get_service(self):
        return create_gradable_solution

    def perform_create(self, serializer):
        service_kwargs = serializer.validated_data
        solution = self.call_service(service_kwargs=service_kwargs)

        if solution:
            serializer.instance = solution
            start_grader_communication(solution.id, 'competitions.Solution')


class CreateNonGradableSolutionApiView(LoginRequiredMixin,
                                       CompetitionViewMixin,
                                       CreateSolutionApiMixin,
                                       CallServiceMixin,
                                       generics.CreateAPIView):
    serializer_class = CompetitionSolutionSerializer
    permission_classes = (IsParticipantInCompetitionApiPerimission, )

    def get_service(self):
        return create_non_gradable_solution

    def perform_create(self, serializer):
        service_kwargs = serializer.validated_data

        self.call_service(service_kwargs=service_kwargs)


class AllParticipantsSolutionsView(LoginRequiredMixin,
                                   CompetitionViewMixin,
                                   IsJudgeInCompetitionPermisssion,
                                   ListView):
    template_name = 'competitions/all_participants_solutions.html'

    def get_queryset(self):
        task = get_object_or_404(CompetitionTask, id=self.kwargs.get('task_id'))
        filters = {
            'solutions__task': task,
            'solutions__status': Solution.OK
        }
        queryset = self.competition.participants.filter(**filters).select_related('profile')
        return queryset.prefetch_related('solutions__task').distinct()


class ParticipantSolutionsView(LoginRequiredMixin,
                               CompetitionViewMixin,
                               IsParticipantInCompetitionPermission,
                               ListView):
    template_name = 'competitions/participant_solutions.html'

    def get_queryset(self):
        user = self.request.user
        self.task = get_object_or_404(CompetitionTask, id=self.kwargs.get('task_id'))

        return Solution.objects.filter(participant=user.competitionparticipant, task=self.task)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task'] = self.task

        return context


class SolutionDetailApiView(generics.RetrieveAPIView):
    serializer_class = CompetitionSolutionSerializer
    permission_classes = (IsParticipantOrJudgeInCompetitionApiPermission, )
    queryset = Solution.objects.all()
    lookup_url_kwarg = 'solution_id'
