$(document).ready(function () {
    let candidateChart = null;
    let participationChart = null;
    let lastRenderKey = null;

    const asNumber = (v) => {
        const n = Number(v);
        return Number.isFinite(n) ? n : 0;
    };

    function destroyCharts() {
        if (candidateChart) candidateChart.destroy();
        if (participationChart) participationChart.destroy();
    }

    function renderCharts(data) {
        destroyCharts();

        const participation = data.participation || {};
        const participantes = asNumber(participation.participantes);
        const abstencionistas = asNumber(participation.abstencionistas);
        const chartCandidates = Array.isArray(data.candidates) ? data.candidates : [];
        const hasCandidateData = data.voting_closed && chartCandidates.some(c => asNumber(c.votos) > 0);
        const hasParticipationData = (participantes + abstencionistas) > 0;

        $('#candidateChart').toggle(hasCandidateData || !data.voting_closed);
        $('#candidate_chart_empty').toggle(!hasCandidateData && data.voting_closed);
        $('#participationChart').toggle(hasParticipationData);
        $('#participation_chart_empty').toggle(!hasParticipationData);

        const candidateCtx = document.getElementById('candidateChart').getContext('2d');
        candidateChart = new Chart(candidateCtx, {
            type: 'bar',
            data: {
                labels: data.voting_closed ? chartCandidates.map(c => c.nombre) : ['Oculto'],
                datasets: [{
                    label: data.voting_closed ? 'Votos por candidato' : 'Resultados ocultos',
                    data: data.voting_closed ? chartCandidates.map(c => asNumber(c.votos)) : [0],
                    backgroundColor: 'rgba(30, 112, 191, 0.22)',
                    borderColor: 'rgba(30, 112, 191, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } },
                    x: { ticks: { maxRotation: 40, minRotation: 0 } }
                }
            }
        });

        const pCtx = document.getElementById('participationChart').getContext('2d');
        participationChart = new Chart(pCtx, {
            type: 'doughnut',
            data: {
                labels: ['Participacion', 'Abstencion'],
                datasets: [{
                    data: [participantes, abstencionistas],
                    backgroundColor: ['rgba(25, 135, 84, 0.32)', 'rgba(220, 53, 69, 0.30)'],
                    borderColor: ['rgba(25, 135, 84, 0.9)', 'rgba(220, 53, 69, 0.9)'],
                    borderWidth: 1
                }]
            },
            options: {
                maintainAspectRatio: false,
                cutout: '62%',
                plugins: { legend: { position: 'top' } }
            }
        });
    }

    function fetchData() {
        $.get('/votaciones/api/voting-stats', function (data) {
            $('#candidate_stats').html('');

            const participation = data.participation || {};
            const tasaParticipacion = asNumber(participation.tasa_participacion);
            const tasaAbstencion = asNumber(participation.tasa_abstencionismo);
            const participantes = asNumber(participation.participantes);
            const abstencionistas = asNumber(participation.abstencionistas);
            const candidates = Array.isArray(data.candidates) ? data.candidates : [];

            if (data.voting_closed && !data.is_viewer) {
                $('#candidate_hidden_notice').hide();
                candidates.forEach(function (candidate) {
                    const porcentaje = asNumber(candidate.porcentaje);
                    $('#candidate_stats').append(
                        '<div><p class="text-large">' + candidate.nombre + ': ' + porcentaje.toFixed(2) + '%</p>' +
                        '<img src="/votaciones_backend/static/uploads/' + candidate.imagen + '" class="party-image" alt="Imagen de ' + candidate.nombre + '"></div>'
                    );
                });
            } else {
                $('#candidate_hidden_notice').show();
            }

            $('#participation')
                .removeClass('kpi-abstention')
                .addClass('kpi-participation')
                .html('<span class="kpi-value">' + tasaParticipacion.toFixed(2) + '%</span><span class="kpi-label">Participación</span>');
            $('#abstention')
                .removeClass('kpi-participation')
                .addClass('kpi-abstention')
                .html('<span class="kpi-value">' + tasaAbstencion.toFixed(2) + '%</span><span class="kpi-label">Abstención</span>');
            $('#quick_participantes').text(participantes);
            $('#quick_abstencionistas').text(abstencionistas);

            const renderKey = JSON.stringify({
                voting_closed: !!data.voting_closed,
                is_viewer: !!data.is_viewer,
                candidates: candidates.map(c => [c.nombre, asNumber(c.votos), c.imagen]),
                participation: [participantes, abstencionistas, tasaParticipacion, tasaAbstencion]
            });

            if (renderKey !== lastRenderKey) {
                renderCharts(data);
                lastRenderKey = renderKey;
            }
        });
    }

    fetchData();
    setInterval(fetchData, 12000);
});
