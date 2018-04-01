Vue.options.delimiters = ['[[', ']]'];

const TableStatus = Object.freeze({CALLING: 0, CORRECTING: 1, IDLE: 2});
const TableStatusName = ['Calling', 'Coordination', 'Idle'];

let queues_model = {
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
                queues_component.$forceUpdate();
            })
            .catch(error => {
                console.log(error);
            });
    }
};
queues_model.update();

Vue.component('team-in-queue', {
  props: ['team', 'expected_duration'],
  template: `
<div :style="'height: ' + expected_duration/20 + 'px'">[[ team ]]</div>`
});

const queues_component = new Vue({
    el: '#queues',
    data: {
        tables: queues_model.tables,
        TableStatus: TableStatus,
        TableStatusName: TableStatusName,
    },
    methods: {
        human_readable_time: function(timestamp) {
            var date = new Date(timestamp*1000);
            var hours = date.getHours();
            var minutes = "0" + date.getMinutes();
            var seconds = "0" + date.getSeconds();
            return hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);
        }
    }
});
