Vue.options.delimiters = ['[[', ']]'];

const TableStatus = Object.freeze({CALLING: 0, CORRECTING: 1, IDLE: 2});
const TableStatusName = ['Calling', 'Coordination', 'Idle'];
const SECOND_IN_PIXELS = 0.05;

let queues_model = {
    tables: [],
    last_update: -1,
    update() {
        return axios.get('/tables/get_all', {params: {last_update: this.last_update}})
            .then(response => {
                if (!response.data.ok) {
                    console.log('TODO');
                    return;
                }
                if (!response.data.changed) return;
                this.last_update = response.data.last_update;
                Object.assign(this.tables, JSON.parse(response.data.tables));
            })
            .catch(error => {
                console.log(error);
            });
    }
};
queues_model.update().then(() => {
    queues_component.$forceUpdate();
});

Vue.component('team-in-queue', {
    props: ['team', 'expected_duration', 'start_time'],
    computed: {
        height: function() {
            return this.expected_duration * SECOND_IN_PIXELS - 1;
        },
        top_pos: function() {
            let now = new Date().getTime() / 1000;
            return (this.start_time - now) * SECOND_IN_PIXELS;
        },
    },
    template: `
<div class='team-in-queue'
     :style='"height: " + height + "px; line-height: " + height + "px; top: " + top_pos + "px"'>[[ team ]]</div>`
});

let queues_component = new Vue({
    el: '#queues',
    data: {
        tables: queues_model.tables,
        TableStatus: TableStatus,
        TableStatusName: TableStatusName,
    },
    computed: {
        start_time: function() {
            let result = {};
            for (let table of this.tables) {
                result[table.name] = {};
                let now =  new Date().getTime() / 1000; // In seconds.
                let curr = undefined;
                let start_time = table.current_coordination_start_time;
                let expected_duration = table.expected_duration;
                    
                if (table.status == TableStatus.CALLING) curr = now;
                else if (table.status == TableStatus.IDLE) curr = now + 300;
                else if (table.status == TableStatus.CORRECTING) {
                    curr = Math.max(now + 300, start_time + expected_duration)
                }
                for (let team of table.queue) {
                    result[table.name][team] = curr;
                    curr += expected_duration;
                }
            }
            return result;
        },
    },
});

Vue.component('queue-header', {
    props: ['table',],
    computed: {
        correcting: function() {
            return this.table.status === TableStatus.CORRECTING;
        },
        calling: function() {
            return this.table.status == TableStatus.CALLING;
        },
        idle: function() {
            return this.table.status == TableStatus.IDLE;
        },
        status_name: function() {
            if (this.correcting) return 'correcting';
            if (this.calling) return 'calling';
            if (this.idle) return 'idle';
        },
        height: function() {
            return this.expected_duration * SECOND_IN_PIXELS - 1;
        },
        top_pos: function() {
            let now = new Date().getTime() / 1000;
            return (this.start_time - now) * SECOND_IN_PIXELS;
        },
    },
    methods: {
        human_readable_time: function(timestamp) {
            var date = new Date(timestamp*1000);
            var hours = date.getHours();
            var minutes = "0" + date.getMinutes();
            var seconds = "0" + date.getSeconds();
            return hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);
        }
    },
    template: `
<div v-bind:class='"queue-header " + [[status_name]]'>
    <div class='queue-header-container'>
        <div class='table-name'>[[ table.name ]]</div>
        <div class='correcting' v-if='correcting'> [[ table.current_coordination_team ]] </div>
        <div class='calling' v-if='calling'> calling </div>
        <div class='idle' v-if='idle'> idle </div>
    </div>
</div>`,
});
