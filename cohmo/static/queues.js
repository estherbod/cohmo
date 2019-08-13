Vue.options.delimiters = ['[[', ']]'];

const TableStatus = Object.freeze({CALLING: 0, CORRECTING: 1, BUSY: 2});
const TableStatusName = ['Calling', 'Coordination', 'Busy'];
const SECOND_IN_PIXELS = 0.05;
const UPDATE_INTERVAL = 10; // in seconds

let queues_model = {
    tables: [],
    last_update: -1,
    update() {
        return axios.get(APPLICATION_ROOT + 'tables/get_all', {params: {last_update: this.last_update}})
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

function update_queues() {
    queues_model.update().then(() => {
        let now = Math.max(START_TIME, new Date().getTime() / 1000);
        now += Math.floor(Math.random() * 10);
        queues_component.now = now;
        schedule_times_component.now = now;
        queues_component.$forceUpdate();
        schedule_times_component.$forceUpdate();
    });
}

update_queues();
setInterval(update_queues, UPDATE_INTERVAL * 1000);


const SCHEDULE_TIMES_INTERVAL = 20*60;
const TIMEZONE_OFFSET = 2;
let schedule_times_component = new Vue({
    el: '#schedule-times',
    data: {
        now: 0,
        tables: queues_model.tables,
    },
    methods: {
        timestamp2hhmm: function(timestamp) {
            let date = new Date(timestamp*1000);
            let hours = date.getUTCHours();
            hours = (hours + TIMEZONE_OFFSET) % 24;
            let minutes = "0" + date.getUTCMinutes();
            return hours + ':' + minutes.substr(-2);
        },
        estimated_finish_time: function() {
            let max_total_duration = 0;
            for (let table of this.tables) {
                max_total_duration = Math.max(
                    max_total_duration,
                    table.queue.length * table.expected_duration);
            }
            for (let bt of BREAK_TIMES) {
                max_total_duration +=
                    Math.max(parseInt(bt[1]), this.now)
                    - Math.max(parseInt(bt[0]), this.now);
            }
            return this.now + max_total_duration + 20 * 60;
        },
        times: function() {
            if (this.now == 0) return []; // To avoid hanging on initialization.
            let curr = Math.ceil((this.now + 120) / SCHEDULE_TIMES_INTERVAL);
            curr = curr * SCHEDULE_TIMES_INTERVAL;

            res = [];
            const finish = this.estimated_finish_time();
            while (curr < finish
                   || curr <= this.now + 2*SCHEDULE_TIMES_INTERVAL) {
                res.push({
                    timestamp: curr,
                    height: (curr-this.now) * (SECOND_IN_PIXELS),
                    human_time: this.timestamp2hhmm(curr),
                });
                curr += SCHEDULE_TIMES_INTERVAL;
            }
            return res;
        },
    },
});

Vue.component('team-in-queue', {
    props: ['team', 'expected_duration', 'start_time', 'now'],
    computed: {
        height: function() {
            return this.expected_duration * SECOND_IN_PIXELS - 1;
        },
        top_pos: function() {
            return (this.start_time - this.now) * SECOND_IN_PIXELS;
        },
    },
    template: `
<div class='team-container'
    :style='"height: " + (height-2) + "px; line-height: " + (height-2) + "px; top: " + (top_pos+2) + "px"'>
    <div class='team-in-queue team'>[[ team ]]</div>
</div>`
});

let queues_component = new Vue({
    el: '#queues',
    data: {
        now: 0, // In seconds
        tables: queues_model.tables,
        TableStatus: TableStatus,
        TableStatusName: TableStatusName,
    },
    computed: {
        start_time: function() {
            this.now;
            let result = {};
            for (let table of this.tables) {
                result[table.name] = {};
                let curr = undefined;
                let start_time = table.current_coordination_start_time;
                let expected_duration = table.expected_duration;
                    
                if (table.status == TableStatus.CALLING) curr = this.now;
                else if (table.status == TableStatus.BUSY) curr = this.now + 300;
                else if (table.status == TableStatus.CORRECTING) {
                    curr = Math.max(this.now + 300, start_time + expected_duration)
                }
                for (let team of table.queue) {
                    for (let bt of BREAK_TIMES) {
                        bt_start = parseInt(bt[0]);
                        bt_end = parseInt(bt[1]);
                        if (bt_start - 300 <= curr && curr <= bt_end) {
                            curr = bt_end;
                        }
                    }
                    result[table.name][team] = curr;
                    curr += expected_duration;
                }
            }
            return result;
        },
        problems: function() {
            this.now;
            let problems = [];
            let problem = {};
            for (let table of this.tables) {
                if (problem.name == table.problem) {
                    problem.tables.push(table);
                    problem.width += 100;
                }
                else {
                    if (problem.name != null) {
                        problems.push(problem);
                    }
                    problem = {};
                    problem.name = table.problem;
                    problem.tables = [table];
                    problem.width = 100 + 10;
                }
            }
            if (problem.name != null) {
                problems.push(problem);
            }
            return problems;
        },
        max_queue_size: function() {
            this.now;
            let max_queue_size = 0;
            for (let table of this.tables) {
                max_queue_size = Math.max(max_queue_size, table.queue.length * table.expected_duration);
            }
            for (let bt of BREAK_TIMES) {
                max_queue_size +=
                    Math.max(parseInt(bt[1]), this.now) - Math.max(parseInt(bt[0]), this.now);
            }
            return max_queue_size * SECOND_IN_PIXELS;
        }
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
        busy: function() {
            return this.table.status == TableStatus.BUSY;
        },
        status_name: function() {
            if (this.correcting) return 'correcting';
            if (this.calling) return 'calling';
            if (this.busy) return 'busy';
        },
    },
    template: `
<div v-bind:class='"queue-header " + [[status_name]]'>
    <div class='queue-header-container'>
        <div class='table-name'>[[ table.name ]]</div>
        <div class='correcting team' v-if='correcting'> [[ table.current_coordination_team ]] </div>
        <div class='calling' v-if='calling'> calling </div>
        <div class='busy' v-if='busy'> busy </div>
    </div>
</div>`,
});
