Vue.options.delimiters = ['[[', ']]'];

const TableStatus = Object.freeze({CALLING: 0, CORRECTING: 1, BUSY: 2});
const TableStatusName = ['calling', 'correcting', 'busy'];

let table_model = {
    data: {
        name: 'TEST',
        problem: '',
        coordinators: '',
        status: 0,
        current_coordination_start_time: 0,
        current_coordination_team: '',
        queue: [],
        TableStatus: TableStatus,
        TableStatusName: TableStatusName,
    },
    update() {
        return axios.get(APPLICATION_ROOT + 'table/' + table_name + '/get_all')
            .then(response => {
                if (!response.data.ok) {
                    console.log('TODO');
                    return;
                }
                Object.assign(this.data, JSON.parse(response.data.table_data));
            })
            .catch(error => {
                console.log(error);
            });
    },
};

table_model.update()
    .then(function() {
        document.getElementsByTagName('body')[0].classList.remove('hidden');
        content_comp.team_coordination = table_model.data.queue[0];
        content_comp.team_calling = table_model.data.queue[0];
    });

new Vue({
    el: '#header',
    data: table_model.data,
});

const TIMEZONE_OFFSET = 2;
let content_comp = new Vue({
    el: '#content',
    data: {
        table: table_model.data,
        TableStatus: TableStatus,
        TableStatusName: TableStatusName,
        call_next: true,
        team_coordination: '',
        team_calling: '',
        temporary_freezed: false,
    },
    computed: {
        human_current_coordination_start_time: function() {
            let date = new Date(this.table.current_coordination_start_time*1000);
            let hours = date.getUTCHours();
            hours = (hours + TIMEZONE_OFFSET) % 24;
            let minutes = "0" + date.getUTCMinutes();
            return hours + ':' + minutes.substr(-2);
        },
    },
    methods: {
        disable_buttons: function(event) {
            this.temporary_freezed = true;
        },
        enable_buttons: function(event) {
            this.temporary_freezed = false;
        },
        before_action: function(event) {
            this.disable_buttons(event);
        },
        after_action: function(event) {
            this.enable_buttons(event);
            table_model.update().then(() => {
                this.team_coordination = table_model.data.queue[0];
                this.team_calling = table_model.data.queue[0];
            });
        },
        start_coordination: function(event) {
            this.before_action(event);
            axios.post(APPLICATION_ROOT + 'table/' + table_name + '/start_coordination',
                       {'team': this.team_coordination})
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        this.enable_buttons(event);
                        return;
                    }
                    this.start_time_coordination = 
                    this.call_next = true;
                    this.after_action(event);
                })
        },
        finish_coordination: function(event) {
            this.before_action(event);
            axios.post(APPLICATION_ROOT + 'table/' + table_name + '/finish_coordination')
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        this.enable_buttons(event);
                        return;
                    }
                    if (this.call_next) {
                        this.switch_to_calling(event);
                    }
                    this.after_action(event);
                })
                .catch(error => {
                    console.log(error);
                });
        },
        pause_coordination: function(event) {
            this.before_action(event);
            axios.post(APPLICATION_ROOT + 'table/' + table_name + '/pause_coordination')
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        this.enable_buttons(event);
                        return;
                    }
                    this.after_action(event);
                })
                .catch(error => {
                    console.log(error);
                });
        },
        switch_to_calling: function(event) {
            this.before_action(event);
            axios.post(APPLICATION_ROOT + 'table/' + table_name + '/switch_to_calling')
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        this.enable_buttons(event);
                        return;
                    }
                    this.after_action(event);
                })
                .catch(error => {
                    console.log(error);
                });
        },
        call_team: function(event) {
            this.before_action(event);
            axios.post(APPLICATION_ROOT + 'table/' + table_name + '/call_team',
                       {'team': this.team_calling})
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        this.enable_buttons(event);
                        return;
                    }
                    this.after_action(event);
                })
        },
        skip_to_next: function(event) {
            this.before_action(event);
            axios.post(APPLICATION_ROOT + 'table/' + table_name + '/skip_to_next')
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        this.enable_buttons(event);
                        return;
                    }
                    this.after_action(event);
                })
                .catch(error => {
                    console.log(error);
                });
        },
        switch_to_busy: function(event) {
            this.before_action(event);
            axios.post(APPLICATION_ROOT + 'table/' + table_name + '/switch_to_busy')
                .then(response => {
                    if (!response.data.ok) {
                        alert(response.data.message);
                        this.enable_buttons(event);
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
