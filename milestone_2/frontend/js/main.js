document.addEventListener('DOMContentLoaded', () => {
    const page = window.location.pathname.split('/').pop();

    bindLogin();
    bindUpload('cv-upload-input');
    bindUpload('cv-upload-main');

    if (page === 'index.html' || page === '') {
        loadDashboardData();
    }
    if (page === 'candidates.html') {
        loadCandidatesData();
    }
    if (page === 'reports.html') {
        loadReportsData();
    }
    if (page === 'profile.html') {
        loadProfileData();
    }
});

const API_BASE = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') && window.location.port === '5500'
    ? 'http://127.0.0.1:5000'
    : '';

function apiUrl(path) {
    return `${API_BASE}${path}`;
}

async function apiGet(url) {
    const response = await fetch(apiUrl(url));
    return parseApiResponse(response);
}

async function parseApiResponse(response) {
    const contentType = response.headers.get('content-type') || '';

    if (contentType.includes('application/json')) {
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.error || `Request failed: ${response.status}`);
        }
        return payload;
    }

    const text = await response.text();
    if (text.toLowerCase().includes('the page could not be found')) {
        throw new Error('Backend API is not available on this deployment. Run the Flask backend to use upload and analysis APIs.');
    }

    const snippet = text.replace(/\s+/g, ' ').slice(0, 120);
    throw new Error(`Unexpected API response (${response.status}): ${snippet}`);
}

function bindLogin() {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;

    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        window.location.href = 'index.html';
    });
}

function bindUpload(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(apiUrl('/api/upload'), {
                method: 'POST',
                body: formData
            });
            const payload = await parseApiResponse(response);

            if (payload && payload.candidate_id) {
                localStorage.setItem('talashLastCandidateId', String(payload.candidate_id));
            }

            alert(`CV uploaded successfully for candidate ID ${payload.candidate_id}.`);

            const path = window.location.pathname;
            const uploadedId = payload?.candidate_id;

            if (path.endsWith('analysis.html') && uploadedId) {
                window.location.href = `analysis.html?id=${uploadedId}`;
                return;
            }

            if (path.endsWith('profile.html') && uploadedId) {
                window.location.href = `profile.html?id=${uploadedId}`;
                return;
            }

            if (path.endsWith('index.html')) {
                loadDashboardData();
            }
            if (path.endsWith('candidates.html')) {
                loadCandidatesData();
            }
        } catch (error) {
            alert(`Upload failed: ${error.message}`);
        } finally {
            input.value = '';
        }
    });
}

async function loadDashboardData() {
    try {
        const [stats, candidates] = await Promise.all([
            apiGet('/api/dashboard-stats'),
            apiGet('/api/candidates')
        ]);

        const candidateList = Array.isArray(candidates.candidates) ? candidates.candidates : [];

        const statNumbers = document.querySelectorAll('.stat-number');
        if (statNumbers.length >= 3) {
            statNumbers[0].innerHTML = `${stats.total_candidates} <span class="increase">LIVE</span>`;
            statNumbers[1].innerHTML = `${stats.analysis_complete} <span class="percentage">${stats.completion_rate}</span>`;
            statNumbers[2].innerHTML = `${stats.flagged} <span class="action-required">[ACTION REQUIRED]</span>`;
        }

        const tableBody = document.querySelector('.analysis-queue table tbody');
        if (tableBody) {
            tableBody.innerHTML = '';
            candidateList.slice(0, 5).forEach((candidate) => {
                const initials = candidate.name
                    .split(' ')
                    .map(part => part[0])
                    .join('')
                    .slice(0, 2)
                    .toUpperCase();

                const statusClass = candidate.status === 'COMPLETE' ? 'complete' : 'pending';
                const score = candidate.score_display || (typeof candidate.score === 'number' ? `${candidate.score}/100` : '--/100');
                tableBody.insertAdjacentHTML('beforeend', `
                    <tr>
                        <td><strong>${initials}</strong> ${candidate.name}<br><small>${candidate.email}</small></td>
                        <td>${new Date().toISOString().slice(0, 10)}</td>
                        <td><span class="status ${statusClass}">${candidate.status}</span></td>
                        <td>${score}</td>
                        <td><a href="analysis.html?id=${candidate.id}">View Analysis</a></td>
                    </tr>
                `);
            });
        }

        const pageInfo = document.getElementById('dashboardPageInfo');
        if (pageInfo) {
            pageInfo.textContent = `DISPLAYING ${Math.min(candidateList.length, 5)} OF ${stats.total_candidates} CANDIDATE RECORDS`;
        }
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

async function loadCandidatesData() {
    try {
        const payload = await apiGet('/api/candidates');
        const tableBody = document.querySelector('table tbody');
        if (!tableBody) return;

        tableBody.innerHTML = '';
        payload.candidates.forEach((candidate) => {
            const initials = candidate.name
                .split(' ')
                .map(part => part[0])
                .join('')
                .slice(0, 2)
                .toUpperCase();

            const statusClass = candidate.status === 'COMPLETE' ? 'complete' : 'pending';
            const score = candidate.score_display || (typeof candidate.score === 'number' ? `${candidate.score}/100` : '--/100');

            tableBody.insertAdjacentHTML('beforeend', `
                <tr>
                    <td><a href="profile.html?id=${candidate.id}"><strong>${initials}</strong> ${candidate.name}</a><br><small>${candidate.email}</small></td>
                    <td>${new Date().toISOString().slice(0, 10)}</td>
                    <td><span class="status ${statusClass}">${candidate.status}</span></td>
                    <td>${score}</td>
                    <td><a href="analysis.html?id=${candidate.id}" title="View Analysis">View Analysis</a></td>
                </tr>
            `);
        });

        const pageInfo = document.querySelector('.pagination span');
        if (pageInfo) {
            pageInfo.textContent = `DISPLAYING ${payload.candidates.length} OF ${payload.total} CANDIDATE RECORDS`;
        }
    } catch (error) {
        console.error('Failed to load candidates data:', error);
    }
}

function destroyChart(chartInstance) {
    if (chartInstance && typeof chartInstance.destroy === 'function') {
        chartInstance.destroy();
    }
}

function renderChart(canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        return null;
    }

    if (typeof Chart === 'undefined') {
        const container = canvas.parentElement;
        if (container && !container.querySelector('.chart-fallback')) {
            const fallback = document.createElement('div');
            fallback.className = 'chart-fallback';
            fallback.textContent = 'Chart data is ready, but the chart library did not load.';
            container.appendChild(fallback);
        }
        return null;
    }

    const existing = canvas.__chartInstance;
    destroyChart(existing);
    const chartInstance = new Chart(canvas, config);
    canvas.__chartInstance = chartInstance;
    return chartInstance;
}

async function loadReportsData() {
    try {
        const payload = await apiGet('/api/reports-data');

        const statNumbers = document.querySelectorAll('.stats .stat-number');
        if (statNumbers.length >= 3) {
            statNumbers[0].textContent = payload.average_score || '0';
            statNumbers[1].textContent = payload.flagged_profiles ?? '0';
            statNumbers[2].textContent = payload.complete_profiles ?? '0';
        }

        const scoreLabels = payload.score_distribution?.labels || [];
        const scoreValues = payload.score_distribution?.values || [];
        const completionLabels = payload.completion_status?.labels || [];
        const completionValues = payload.completion_status?.values || [];
        const pipelineLabels = payload.pipeline_status?.labels || [];
        const completedValues = payload.pipeline_status?.completed || [];
        const processingValues = payload.pipeline_status?.processing || [];
        const skillLabels = payload.top_skills?.labels || [];
        const skillValues = payload.top_skills?.values || [];

        renderChart('scoreChart', {
            type: 'bar',
            data: {
                labels: scoreLabels,
                datasets: [{
                    label: 'Candidates',
                    data: scoreValues,
                    backgroundColor: '#0f1b2d',
                    borderRadius: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } },
            },
        });

        renderChart('completionChart', {
            type: 'doughnut',
            data: {
                labels: completionLabels,
                datasets: [{
                    data: completionValues,
                    backgroundColor: ['#0f1b2d', '#d4a574', '#c8d3df'],
                    borderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
            },
        });

        renderChart('statusChart', {
            type: 'line',
            data: {
                labels: pipelineLabels,
                datasets: [
                    {
                        label: 'Completed',
                        data: completedValues,
                        borderColor: '#1d8f65',
                        backgroundColor: 'rgba(29, 143, 101, 0.16)',
                        tension: 0.35,
                        fill: true,
                    },
                    {
                        label: 'Processing',
                        data: processingValues,
                        borderColor: '#d4a574',
                        backgroundColor: 'rgba(212, 165, 116, 0.16)',
                        tension: 0.35,
                        fill: true,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
            },
        });

        renderChart('skillsChart', {
            type: 'bar',
            data: {
                labels: skillLabels,
                datasets: [{
                    label: 'Mentions',
                    data: skillValues,
                    backgroundColor: '#15253c',
                    borderRadius: 6,
                }],
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true } },
            },
        });

        const hasAnyChartData = [scoreValues, completionValues, completedValues, skillValues].some(values => Array.isArray(values) && values.length > 0);
        if (!hasAnyChartData) {
            document.querySelectorAll('.chart-container').forEach((container) => {
                if (!container.querySelector('.chart-fallback')) {
                    const fallback = document.createElement('div');
                    fallback.className = 'chart-fallback';
                    fallback.textContent = 'No report data available yet. Upload a CV to populate this chart.';
                    container.appendChild(fallback);
                }
            });
        }

        const reportsTableBody = document.querySelector('.analysis-queue:last-of-type table tbody');
        if (reportsTableBody && Array.isArray(payload.reports)) {
            reportsTableBody.innerHTML = '';
            payload.reports.forEach((report) => {
                const statusClass = report.status === 'READY' ? 'complete' : report.status === 'PROCESSING' ? 'processing' : 'pending';
                reportsTableBody.insertAdjacentHTML('beforeend', `
                    <tr>
                        <td>${report.name || 'Untitled Report'}</td>
                        <td>${report.analysis_type || 'Generated Output'}</td>
                        <td>${report.date || ''}</td>
                        <td><span class="status ${statusClass}">${report.status || 'PENDING'}</span></td>
                    </tr>
                `);
            });
        }
    } catch (error) {
        console.error('Failed to load reports data:', error);
    }
}

async function loadProfileData() {
    const params = new URLSearchParams(window.location.search);
    const candidateId = params.get('id') || '1';

    try {
        let candidate = null;
        let analysis = null;

        const candidateResponse = await fetch(apiUrl(`/api/candidate/${candidateId}`));
        if (candidateResponse.ok) {
            candidate = await candidateResponse.json();
        }

        const analysisResponse = await fetch(apiUrl(`/api/analysis-output/${candidateId}`));
        if (analysisResponse.ok) {
            analysis = await analysisResponse.json();
        }

        if (!candidate) {
            const list = await apiGet('/api/candidates');
            if (Array.isArray(list.candidates) && list.candidates.length > 0) {
                const fallbackId = list.candidates[0].id;
                const fallbackResponse = await fetch(apiUrl(`/api/candidate/${fallbackId}`));
                if (fallbackResponse.ok) {
                    candidate = await fallbackResponse.json();
                }
                const fallbackAnalysisResponse = await fetch(apiUrl(`/api/analysis-output/${fallbackId}`));
                if (fallbackAnalysisResponse.ok) {
                    analysis = await fallbackAnalysisResponse.json();
                }
            }
        }

        if (!candidate) {
            const profileName = document.getElementById('profileName');
            if (profileName) profileName.textContent = 'No candidate found';
            const profileSummaryBody = document.getElementById('profileSummaryBody');
            if (profileSummaryBody) {
                profileSummaryBody.innerHTML = '<tr><td colspan="2">Upload a CV to generate a profile view.</td></tr>';
            }
            return;
        }

        const candidateName = candidate.name || analysis?.candidate_name || 'Unknown Candidate';
        const educationList = Array.isArray(candidate.education) ? candidate.education : [];
        const experienceList = Array.isArray(candidate.experience) ? candidate.experience : [];
        const skillList = Array.isArray(candidate.skills) ? candidate.skills : [];
        const missingFields = Array.isArray(analysis?.missing_information?.missing_fields)
            ? analysis.missing_information.missing_fields
            : [];

        const overallScore = Math.max(0, 100 - (missingFields.length * 4));
        const analysisStatus = analysis ? 'COMPLETE' : 'PENDING';
        const flagStatus = missingFields.length > 0 ? 'REVIEW' : 'CLEAR';

        const profileName = document.getElementById('profileName');
        if (profileName) profileName.textContent = candidateName;

        const profileScore = document.getElementById('profileScore');
        if (profileScore) profileScore.textContent = `${overallScore}`;

        const profileAnalysisStatus = document.getElementById('profileAnalysisStatus');
        if (profileAnalysisStatus) profileAnalysisStatus.textContent = analysisStatus;

        const profileFlagStatus = document.getElementById('profileFlagStatus');
        if (profileFlagStatus) profileFlagStatus.textContent = flagStatus;

        const profileSummaryBody = document.getElementById('profileSummaryBody');
        if (profileSummaryBody) {
            const educationText = educationList.length > 0
                ? educationList.map((item) => [item.degree_name, item.institution_name].filter(Boolean).join(' - ') || 'Education').join(', ')
                : 'No education records available';
            const experienceText = experienceList.length > 0
                ? experienceList.map((item) => item.job_title || 'Experience').join(', ')
                : 'No experience records available';
            const skillText = skillList.length > 0
                ? skillList.map((item) => item.skill_name || 'Skill').join(', ')
                : 'No skills recorded';

            profileSummaryBody.innerHTML = `
                <tr><td>Education</td><td>${educationText}</td></tr>
                <tr><td>Experience</td><td>${experienceText}</td></tr>
                <tr><td>Skills</td><td>${skillText}</td></tr>
            `;
        }

        const downloadButton = document.getElementById('downloadProfileBtn');
        if (downloadButton && !downloadButton.dataset.bound) {
            downloadButton.dataset.bound = 'true';
            downloadButton.addEventListener('click', () => {
                const payload = {
                    candidate,
                    analysis,
                    exported_at: new Date().toISOString(),
                };
                const dataBlob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(dataBlob);
                link.download = `profile_${candidateName.replace(/\s+/g, '_').toLowerCase()}.json`;
                link.click();
            });
        }
    } catch (error) {
        console.error('Failed to load profile data:', error);
        const profileName = document.getElementById('profileName');
        if (profileName) profileName.textContent = 'Profile unavailable';
    }
}
