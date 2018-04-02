Vue.options.delimiters = ['[[', ']]'];

const TableStatus = Object.freeze({CALLING: 0, CORRECTING: 1, IDLE: 2});
const TableStatusName = ['Calling', 'Correcting', 'Idle'];

let table_model = {
    data: {
        name: 'TEST',
        problem: '',
        coordinators: '',
        status: 0,
        current_coordination_start_time: 0,
        current_coordination_team: '',
        queue: [],
    },
    update() {
        axios.get('/table/' + table_name + '/get_all')
            .then(response => {
                if (!response.data.ok) {
                    console.log('TODO');
                    return;
                }
                Object.assign(this.data, JSON.parse(response.data.table_data))
            })
            .catch(error => {
                console.log(error);
            });
    }
};

table_model.update();

new Vue({
    el: '#header',
    data: table_model.data,
});

let content_comp = new Vue({
    el: '#content',
    data: {
        table: table_model.data,
        TableStatus: TableStatus,
        TableStatusName: TableStatusName,
        call_next: true,
        team_coordination: table_model.data.queue[0],
    },
    methods: {
        after_action: function(event) {
            table_model.update();
            this.team_coordination = this.table.queue[0];
            table_model.update();
        },
        start_coordination: function(event) {
            axios.post('/table/' + table_name + '/start_coordination',
                       {'team': this.team_coordination})
                .then(response => {
                    if (!response.data.ok) {
                        console.log('TODO')
                        return;
                    }
                    this.after_action(event);
                })
        },
        finish_coordination: function(event) {
            axios.post('/table/' + table_name + '/finish_coordination')
                .then(response => {
                    if (!response.data.ok) {
                        console.log('TODO');
                        return;
                    }
                    if (this.call_next) {
                        content_comp.switch_to_calling(event);
                    }
                    this.after_action(event);
                })
                .catch(error => {
                    console.log(error);
                });
        },
        pause_coordination: function(event) {
            axios.post('/table/' + table_name + '/pause_coordination')
                .then(response => {
                    if (!response.data.ok) {
                        console.log('TODO');
                        return;
                    }
                    this.after_action(event);
                })
                .catch(error => {
                    console.log(error);
                });
        },
        switch_to_calling: function(event) {
            axios.post('/table/' + table_name + '/switch_to_calling')
                .then(response => {
                    if (!response.data.ok) {
                        console.log('TODO');
                        return;
                    }
                    this.after_action(event);
                })
                .catch(error => {
                    console.log(error);
                });
        },
        skip_to_next: function(event) {
            axios.post('/table/' + table_name + '/skip_to_next')
                .then(response => {
                    if (!response.data.ok) {
                        console.log('TODO');
                        return;
                    }
                    this.after_action(event);
                })
                .catch(error => {
                    console.log(error);
                });
        },
        switch_to_idle: function(event) {
            axios.post('/table/' + table_name + '/switch_to_idle')
                .then(response => {
                    if (!response.data.ok) {
                        console.log('TODO');
                        return;
                    }
                    this.after_action(event);
                })
                .catch(error => {
                    console.log(error);
                });
        },
    }
});
