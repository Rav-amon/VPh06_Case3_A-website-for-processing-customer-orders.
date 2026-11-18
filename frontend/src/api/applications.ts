import { apiRequest } from '@/api/client';
import type {
  IApplicationItem,
  IApplicationsPage,
} from '@/types/applications';

/** Очередь заявок с температурой: GET /api/applications/?skip=&limit= */
export function fetchApplications(
  skip = 0,
  limit = 100,
): Promise<IApplicationsPage> {
  const params = new URLSearchParams({
    skip: String(skip),
    limit: String(limit),
  });
  return apiRequest<IApplicationsPage>(
    `/api/applications/?${params.toString()}`,
    { auth: true },
  );
}

/** Одна заявка с блоком intelligence. */
export function fetchApplication(
  applicationId: number,
): Promise<IApplicationItem> {
  return apiRequest<IApplicationItem>(`/api/applications/${applicationId}`, {
    auth: true,
  });
}
