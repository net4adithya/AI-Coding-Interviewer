import api from './api';

export interface Candidate {
    id: number;
    intern_email: string;
    intern_name: string | null;
    assessment_title: string;
    status: string;
    assigned_at: string;
    submitted_at: string | null;
    assessment_id: number;
    intern_id: number;
}

export const getCandidates = async (): Promise<Candidate[]> => {
    const response = await api.get('/interns/candidates');
    return response.data;
};

export const assignCandidateByEmail = async (assessmentId: number, email: string): Promise<any> => {
    const response = await api.post(`/api/v1/assessments/${assessmentId}/assign-email`, { email });
    return response.data;
};
