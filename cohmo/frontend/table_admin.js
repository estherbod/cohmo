let header_model = new Vue({
    el: '#header',
    data: {
        table_name: 'T2',
        coordinators: ['Marco Mengoni', 'Franca Leosini'],
        problem: '1',
    }
});

let content_model = new Vue({
    el: '#content',
    data: {
        status: 'CORRECTING',
        current_coordination_team: 'ITA',
    },
    methods: {
        finish_coordination: function(event) {
            this.status = 'CALLING';
        },
        delay_coordination: function(event) {
            this.status = 'IDLE';
        },
    }
});
