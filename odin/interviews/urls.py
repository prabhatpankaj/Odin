from django.conf.urls import url

from .views import (
    ChooseInterviewView,
    InterviewsListView,
    GenerateInterviewsView,
    CreateFreeTimeView,
    UpdateFreeTimeView,
    DeleteFreeTimeView,
    ConfirmInterviewView,
    FreeInterviewsListAPIView,
    SendInterviewConfirmationEmailsView,
    RateInterviewView,
    AcceptedApplicantsListView,
    PromoteAcceptedUsersToStudentsView
)


urlpatterns = [
    url(
        regex='^choose/(?P<application_id>[0-9]+)/(?P<interview_token>[-\w]+)/$',
        view=ChooseInterviewView.as_view(),
        name='choose-interview'
    ),
    url(
        regex='^$',
        view=InterviewsListView.as_view(),
        name='user-interviews'
    ),
    url(
        regex='^generate-interviews/$',
        view=GenerateInterviewsView.as_view(),
        name='generate-interviews'
    ),
    url(
        regex='^add-free-time/$',
        view=CreateFreeTimeView.as_view(),
        name='add-free-time'
    ),
    url(
        regex='^delete-free-time/(?P<free_time_id>[0-9]+)/$',
        view=DeleteFreeTimeView.as_view(),
        name='delete-free-time'
    ),
    url(
        regex='^edit-free-time/(?P<free_time_id>[0-9]+)/$',
        view=UpdateFreeTimeView.as_view(),
        name='edit-free-time'
    ),
    url(
        regex='^confirm/(?P<application_id>[0-9]+)/(?P<interview_token>[-\w]+)/$',
        view=ConfirmInterviewView.as_view(),
        name='confirm-interview'
    ),
    url(
        regex='^api/get-free-interviews/$',
        view=FreeInterviewsListAPIView.as_view(),
        name='get_free_interviews'
    ),
    url(
        regex='^send-interview-confirmation-emails/$',
        view=SendInterviewConfirmationEmailsView.as_view(),
        name='send-interview-confirmation-emails'
    ),
    url(
        regex='^rate-interview/(?P<interview_token>[-\w]+)/$',
        view=RateInterviewView.as_view(),
        name='rate-interview'
    ),
    url(
        regex='^accepted-applicants/$',
        view=AcceptedApplicantsListView.as_view(),
        name='accepted-applicants'
    ),
    url(
        regex='^assign-accepted-users/$',
        view=PromoteAcceptedUsersToStudentsView.as_view(),
        name='assign-accepted-users'
    )
]
