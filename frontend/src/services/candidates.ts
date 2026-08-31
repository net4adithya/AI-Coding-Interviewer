import api from './api';
import { demoService } from './demoApi';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export interface Candidate {
    id: number | string;
    intern_email: string;
    intern_name: string | null;
    assessment_title: string;
    status: string;
    assigned_at: string;
    submitted_at: string | null;
    assessment_id: number | string;
    intern_id?: number;
}

export const getCandidates = async (): Promise<any[]> => {
    if (DEMO_MODE) return demoService.getCandidates();
    const response = await api.get('/interns/candidates');
    return response.data;
};

export const assignCandidateByEmail = async (assessmentId: number | string, email: string): Promise<any> => {
    if (DEMO_MODE) {
        console.log('[DEMO TRACE] Routing assignCandidateByEmail to /demo/assignments/assign', { assessmentId, email });
        return demoService.assignAssessment(String(assessmentId), email);
    }
    const response = await api.post(`/api/v1/assessments/${assessmentId}/assign-email`, { email });
    return response.data;
};
