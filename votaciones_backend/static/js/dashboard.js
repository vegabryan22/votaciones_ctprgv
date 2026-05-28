$(document).ready(function () {
    let candidateChart = null;
    let participationChart = null;

    function destroyCharts() {
        if (candidateChart) candidateChart.destroy();
        if (participationChart) participationChart.destroy();
    }

    function renderCharts(data) {
        destroyCharts();

        const candidateCtx = document.getElementById('candidateChart').getContext('2d');
        candidateChart = new Chart(candidateCtx, {
            type: 'bar',
            data: {
                labels: data.voting_closed ? data.candidates.map(c => c.nombre) : ['Oculto'],
                datasets: [{
                    label: data.voting_closed ? 'Votos por candidato' : 'Resultados ocultos',
                    data: data.voting_closed ? data.candidates.map(c => c.votos) : [0],
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
                    data: [data.participation.participantes, data.participation.abstencionistas],
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

            if (data.voting_closed && !data.is_viewer) {
                $('#candidate_hidden_notice').hide();
                data.candidates.forEach(function (candidate) {
                    $('#candidate_stats').append(
                        '<div><p class="text-large">' + candidate.nombre + ': ' + candidate.porcentaje + '%</p>' +
                        '<img src="/votaciones_backend/static/uploads/' + candidate.imagen + '" class="party-image" alt="Imagen de ' + candidate.nombre + '"></div>'
                    );
                });
            } else {
                $('#candidate_hidden_notice').show();
            }

            $('#participation').text(data.participation.tasa_participacion + '% Participacion');
            $('#abstention').text(data.participation.tasa_abstencionismo + '% Abstencion');

            renderCharts(data);
        });
    }

    fetchData();
    setInterval(fetchData, 5000);
});
