import api from './api';
import { demoService } from './demoApi';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export interface Submission {
    id: number | string;
    intern_name: string;
    intern_email: string;
    assessment_title: string;
    submitted_at: string;
    language: string;
    ai_review_status: string;
    review_status: string;
    submission_id: number | string;
}

export const getSubmissions = async (): Promise<any[]> => {
    if (DEMO_MODE) return demoService.getSubmissions();
    const response = await api.get('/submissions/');
    return response.data;
};
