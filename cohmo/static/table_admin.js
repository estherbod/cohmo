let table_model = {
    data: {
        name: '',
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

let header_comp = new Vue({
    el: '#header',
    data: table_model.data,
});

let content_comp = new Vue({
    el: '#content',
    data: table_model.data,
    methods: {
        finish_coordination: function(event) {
            this.status = 'CALLING';
        },
        delay_coordination: function(event) {
            this.status = 'IDLE';
        },
    }
});
