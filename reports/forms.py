from django import forms
from .models import IssueReport, IssueComment, IssueCategory


class IssueReportForm(forms.ModelForm):
    class Meta:
        model = IssueReport
        fields = [
            'title', 'category', 'description',
            'location', 'ward_number', 'landmark',
            'priority', 'image', 'image2',
            'latitude', 'longitude'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Brief title of the issue',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe the issue in detail...',
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'Street/Area name in Tumakuru',
                'class': 'form-control'
            }),
            'landmark': forms.TextInput(attrs={
                'placeholder': 'Nearest landmark (optional)',
                'class': 'form-control'
            }),
            'ward_number': forms.Select(
                choices=[('', 'Select Ward')] + [(str(i), f"Ward {i}") for i in range(1, 36)],
                attrs={'class': 'form-select'}
            ),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = IssueCategory.objects.filter(is_active=True)
        self.fields['image'].widget.attrs.update({'class': 'form-control', 'accept': 'image/*'})
        self.fields['image2'].widget.attrs.update({'class': 'form-control', 'accept': 'image/*'})
        self.fields['image2'].required = False


class IssueCommentForm(forms.ModelForm):
    class Meta:
        model = IssueComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Add your comment...',
                'class': 'form-control'
            })
        }
