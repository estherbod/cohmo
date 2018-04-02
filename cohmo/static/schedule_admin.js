Vue.options.delimiters = ['[[', ']]'];

const TableStatus = Object.freeze({CALLING: 0, CORRECTING: 1, IDLE: 2});
const TableStatusName = ['Calling', 'Coordination', 'Idle'];

let schedule_model = {
    tables: {},
    last_update: -1,
    update() {
        axios.get('/tables/get_all', {params: {last_update: this.last_update}})
            .then(response => {
                if (!response.data.ok) {
                    console.log('TODO');
                    return;
                }
                if (!response.data.changed) return;
                this.last_update = response.data.last_update;
                Object.assign(this.tables, JSON.parse(response.data.tables));
                content_comp.$forceUpdate();
            })
            .catch(error => {
                console.log(error);
            });
    }
};
schedule_model.update();

const content_comp = new Vue({
    el: '#content',
    data: {
        tables: schedule_model.tables,
        TableStatus: TableStatus,
        TableStatusName: TableStatusName,
        selected_table: '',
        selected_team: '',
        selected_team1: '',
        selected_team2: '',
        position: '',
    },
    methods: {
        add_to_queue: function(event) {
            axios.post('/table/' + this.selected_table + '/add_to_queue',
                       {'team': this.selected_team, 'pos': this.position})
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message)
                        console.log('TODO')
                        return;
                    }
                    schedule_model.update();
                })
        },
        remove_from_queue: function(event) {
            axios.post('/table/' + this.selected_table + '/remove_from_queue',
                       {'team': this.selected_team})
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message)
                        console.log('TODO')
                        return;
                    }
                    schedule_model.update();
                })
        },
        swap_teams_in_queue: function(event) {
            axios.post('/table/' + this.selected_table + '/swap_teams_in_queue',
                       {'teams': [this.selected_team1, this.selected_team2]})
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message)
                        console.log('TODO')
                        return;
                    }
                    schedule_model.update();
                })
        },
    }
});
