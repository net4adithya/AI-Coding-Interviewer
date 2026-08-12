import api from './api';

export interface Submission {
    id: number;
    intern_name: string;
    intern_email: string;
    assessment_title: string;
    submitted_at: string;
    language: string;
    ai_review_status: string;
    review_status: string;
    submission_id: number;
}

export const getSubmissions = async (): Promise<Submission[]> => {
    const response = await api.get('/submissions/');
    return response.data;
};
