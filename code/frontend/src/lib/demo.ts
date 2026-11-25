// TODO: replace with API data once the backend has user and document management.
export const roles = ['Intern', 'Researcher', 'Admin'];
export const levels = [1, 2, 3, 4, 5, 6];

export const users = [
  {
    id: 1,
    name: 'John Doe',
    email: 'john.doe1@example.com',
    role: 'Researcher',
    status: 'Active',
    seen: 'Today, 09:42',
  },
  {
    id: 2,
    name: 'John Doe',
    email: 'john.doe2@example.com',
    role: 'Intern',
    status: 'Invited',
    seen: 'Not yet joined',
  },
  {
    id: 3,
    name: 'John Doe',
    email: 'john.doe3@example.com',
    role: 'Admin',
    status: 'Active',
    seen: 'Yesterday',
  },
  {
    id: 4,
    name: 'John Doe',
    email: 'john.doe4@example.com',
    role: 'Researcher',
    status: 'Suspended',
    seen: '12 Jun 2025',
  },
];

export const papers = [
  {
    id: 1,
    title: 'Community health outcomes',
    meta: 'A. Morgan · 2025 · PDF',
    level: 1,
    status: 'Published',
    updated: 'Today',
  },
  {
    id: 2,
    title: 'Remote care adoption',
    meta: 'J. Chen · 2025 · PDF',
    level: 2,
    status: 'Published',
    updated: 'Today',
  },
  {
    id: 3,
    title: 'Clinical decision support',
    meta: 'S. Patel · 2024 · PDF',
    level: 3,
    status: 'Published',
    updated: 'Yesterday',
  },
  {
    id: 4,
    title: 'Long-term treatment response',
    meta: 'M. Taylor · 2024 · PDF',
    level: 4,
    status: 'Published',
    updated: '2 days ago',
  },
  {
    id: 5,
    title: 'Patient journey analysis',
    meta: 'R. Garcia · 2025 · PDF',
    level: 5,
    status: 'Draft',
    updated: '3 days ago',
  },
  {
    id: 6,
    title: 'Cross-site research synthesis',
    meta: 'K. Wilson · 2023 · PDF',
    level: 6,
    status: 'Archived',
    updated: '1 week ago',
  },
];

export const resources = [
  { name: 'IMO-003 Biomarker Results.xlsx', meta: '2.4 MB · Updated today', granted: true },
  { name: 'Ovarian Cancer Cohort.xlsx', meta: '8.1 MB · Updated 2 days ago', granted: true },
  { name: 'CRP Longitudinal Study.xlsx', meta: '4.7 MB · Updated 5 days ago', granted: false },
  { name: 'Patient Demographics 2024.xlsx', meta: '1.9 MB · Updated 1 week ago', granted: true },
  { name: 'CA-125 Reference Ranges.xlsx', meta: '780 KB · Updated 2 weeks ago', granted: false },
];
