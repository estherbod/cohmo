Vue.options.delimiters = ['[[', ']]'];

const TableStatus = Object.freeze({CALLING: 0, CORRECTING: 1, BUSY: 2});
const TableStatusName = ['Calling', 'Coordination', 'Busy'];

let schedule_model = {
    tables: {},
    last_update: -1,
    update() {
        axios.get(APPLICATION_ROOT + 'tables/get_all', {params: {last_update: this.last_update}})
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
        add_selected_table: '',
        add_selected_team: '',
        add_position: '',
        remove_selected_table: '',
        remove_selected_team: '',
        swap_selected_table: '',
        swap_selected_team1: '',
        swap_selected_team2: '',
    },
    methods: {
        add_to_queue: function(event) {
            axios.post(APPLICATION_ROOT + 'table/' + this.add_selected_table + '/add_to_queue',
                       {'team': this.add_selected_team, 'pos': this.add_position})
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        return;
                    }
                    schedule_model.update();
                })
        },
        remove_from_queue: function(event) {
            axios.post(APPLICATION_ROOT + 'table/' + this.remove_selected_table + '/remove_from_queue',
                       {'team': this.remove_selected_team})
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        return;
                    }
                    schedule_model.update();
                })
        },
        swap_teams_in_queue: function(event) {
            axios.post(APPLICATION_ROOT + 'table/' + this.swap_selected_table + '/swap_teams_in_queue',
                       {'teams': [this.swap_selected_team1, this.swap_selected_team2]})
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        return;
                    }
                    schedule_model.update();
                })
        },
    }
});
