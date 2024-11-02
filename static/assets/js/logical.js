$(document).ready(function() {
    // Load user data
    function loadUsers() {
        $.get('/admin/Admin-Dashboard', function(data) {
            $('#user-body').empty(); // Clear the current user body

            if (Array.isArray(data)) {
                data.forEach((user,index) => {
                    const displayUserId = index + 1;
                    $('#user-body').append(`
                        <tr>
                            <td>${displayUserId}</td>
                            <td><img src="/static/uploads/${user.ProfilePic}" alt="Profile Picture" class="profile-pic" width="100" data-img="/static/uploads/${user.ProfilePic}"></td>
                            <td>${user.name}</td>
                            <td>${user.address}</td>
                            <td>${user.contact_number}</td>
                            <td>${user.plate_number}</td>
                            <td>${user.roomNumber}</td>
                            <td>${user.email}</td>
                            <td>
                                <button class="btn btn-info view-btn" data-id='${user.userid}'>View Utilities</button>
                                <button class="btn btn-warning edit-btn" data-user='${JSON.stringify(user)}'>Edit</button>
                                <button class="btn btn-danger delete-btn" data-id='${user.userid}'>Delete</button>
                            </td>
                        </tr>
                    `);
                });

                $('#user-table').DataTable(); // Initialize DataTable
            } else {
                alert('Unexpected data format received. Please try again.');
            }
        }).fail(function() {
            alert('Error loading users. Please try again.');
        });
    }

    // View User Utilities Modal
    $(document).on('click', '.view-btn', function() {
        const userId = $(this).data('id');

        $.ajax({
            type: 'POST',
            url: '/admin/Admin-Dashboard',
            contentType: 'application/json',
            data: JSON.stringify({ userid: userId, action: 'view_utilities' }),
            success: function(response) {
                $('#modal-body-utilities').html(`
                    <form id="utilities-form">
                        <input type="hidden" name="login_id" id="login_id" value="${response.login_id}">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="water" name="water" ${response.water ? 'checked' : ''}>
                            <label class="form-check-label" for="water">Water</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="electricity" name="electricity" ${response.electricity ? 'checked' : ''}>
                            <label class="form-check-label" for="electricity">Electricity</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="internet" name="internet" ${response.internet ? 'checked' : ''}>
                            <label class="form-check-label" for="internet">Internet</label>
                        </div>
                    </form>
                `);
                $('#utilities-modal').modal('show');

                $('#save-utilities-btn').off('click').on('click', function() {
                    saveUtilitiesData(userId);
                });
            },
            error: function() {
                alert('Error fetching utilities. Please try again.');
            }
        });
    });

    // Save User Utilities Data
    function saveUtilitiesData(userId) {
        const data = {
            userid: userId,
            login_id: $('#login_id').val(),
            water: $('#water').is(':checked') ? 1 : 0,
            electricity: $('#electricity').is(':checked') ? 1 : 0,
            internet: $('#internet').is(':checked') ? 1 : 0,
            action: 'update_utilities'
        };

        $.ajax({
            type: 'POST',
            url: '/admin/Admin-Dashboard',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                alert(response.status);
                $('#utilities-modal').modal('hide');
                loadUsers(); // Refresh user data
            },
            error: function() {
                alert('Error saving utility data. Please try again.');
            }
        });
    }

    // Add User Modal
    $('#add-btn').click(function() {
        $('#modal-body').html(`
            <form id="user-form">
                <input type="hidden" name="userid" id="userid">
                <div class="form-group">
                    <label for="name">Name</label>
                    <input type="text" class="form-control" name="name" id="name" required>
                </div>
                <div class="form-group">
                    <label for="address">Address</label>
                    <input type="text" class="form-control" name="address" id="address" required>
                </div>
                <div class="form-group">
                    <label for="Contact">Contact Number</label>
                    <input type="text" class="form-control" name="con_user" id="con_user" required>
                </div>
                <div class="form-group">
                    <label for="plate_number">Plate Number</label>
                    <input type="text" class="form-control" name="plate_number" id="plate_number">
                </div>
                <div class="form-group">
                    <label for="roomNumber">Room Number</label>
                    <input type="text" class="form-control" name="roomNumber" id="roomNumber">
                </div>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" class="form-control" name="email" id="email" required>
                </div>
                <div class="form-group">
                    <label for="addpassword">Password</label>
                    <input type="password" class="form-control" name="addpassword" id="addpassword" required>
                </div>
            </form>
        `);
        $('#modalLabel').text('Add User');
        $('#user-modal').modal('show');

        $('#save-btn').off('click').on('click', function() {
            saveUserData('add');
        });
    });

    // Edit User
    $(document).on('click', '.edit-btn', function() {
        const user = $(this).data('user');
        $('#modal-body').html(`
            <form id="user-form">
                <input type="hidden" name="userid" id="userid" value="${user.userid}">
                <div class="form-group">
                    <label for="name">Name</label>
                    <input type="text" class="form-control" name="name" id="name" value="${user.name}" required>
                </div>
                <div class="form-group">
                    <label for="address">Address</label>
                    <input type="text" class="form-control" name="address" id="address" value="${user.address}" required>
                </div>
                <div class="form-group">
                    <label for="Contact">Contact Number</label>
                    <input type="text" class="form-control" name="con_user" id="con_user" value="${user.contact_number}" required>
                </div>
                <div class="form-group">
                    <label for="plate_number">Plate Number</label>
                    <input type="text" class="form-control" name="plate_number" id="plate_number" value="${user.plate_number}">
                </div>
                <div class="form-group">
                    <label for="roomNumber">Room Number</label>
                    <input type="text" class="form-control" name="roomNumber" id="roomNumber" value="${user.roomNumber}">
                </div>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" class="form-control" name="email" id="email" value="${user.email}" required>
                </div>
            </form>
        `);
        $('#modalLabel').text('Edit User');
        $('#user-modal').modal('show');

        $('#save-btn').off('click').on('click', function() {
            saveUserData('update');
        });
    });

    // Save User Data Function
    function saveUserData(action) {
        const data = {
            userid: $('#userid').val(),
            name: $('#name').val(),
            address: $('#address').val(),
            contact_number: $('#con_user').val(),
            plate_number: $('#plate_number').val(),
            roomNumber: $('#roomNumber').val(),
            email: $('#email').val(),
            action: action
        };

        // Include password only if adding a new user
        if (action === 'add') {
            data.password = $('#addpassword').val(); // Get the password for new user
        }

        $.ajax({
            type: 'POST',
            url: '/admin/Admin-Dashboard',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                alert(response.status);
                $('#user-modal').modal('hide');
                loadUsers(); // Refresh user data
            },
            error: function() {
                alert('Error saving user data. Please try again.');
            }
        });
    }

    // Delete User
    $(document).on('click', '.delete-btn', function() {
        const userId = $(this).data('id');
        if (confirm('Are you sure you want to delete this user?')) {
            $.ajax({
                type: 'POST',
                url: '/admin/Admin-Dashboard',
                contentType: 'application/json',
                data: JSON.stringify({ userid: userId, action: 'delete' }),
                success: function(response) {
                    alert(response.status);
                    loadUsers(); // Refresh user data
                },
                error: function() {
                    alert('Error deleting user. Please try again.');
                }
            });
        }
    });

    //profile Pic
    $(document).on('click', '.profile-pic', function() {
        const imgSrc = $(this).data('img');
        $('#full-image').attr('src', imgSrc);
        $('#image-modal').modal('show');
    });

    // Initialize user loading
    loadUsers();

    // Close modals on dismiss
    $(document).on('click', '#utilities-modal [data-dismiss="modal"], #user-modal [data-dismiss="modal"], #image-modal [data-dismiss="modal"]', function() {
        $(this).closest('.modal').modal('hide');
    });
});
