<template>
  <div class="app">
    <header>
      <div class="logo-container">
        <img src="@/assets/HashAgile.png" alt="HashAgile Logo" class="logo" />
      </div>
      <div class="header-text">
        <h1>Candidate List</h1>
        <p>Manage candidate statuses by selecting or rejecting them below.</p>
      </div>
      <!-- Compose Email Button at the top -->
      <div class="compose-email-container-top">
        <button class="btn btn-compose-email" @click="openComposeModal">Compose Email</button>
      </div>
    </header>

    <!-- Filters and Batch Actions -->
    <div class="filters-container">
      <div class="filters">
        <label for="passingYear">Filter by Passing Year:</label>
        <select v-model="passingYear" @change="fetchCandidates">
          <option value="">All</option>
          <option value="2024">2024</option>
          <option value="2025">2025</option>
        </select>

        <label for="round">Filter by Round:</label>
        <select v-model="round" @change="fetchCandidates">
          <option value="">All</option>
          <option value="level1">Level 1</option>
          <option value="level2">Level 2</option>
          <option value="final">Final</option>
        </select>
      </div>

      <div class="batch-actions">
        <button class="btn btn-select-all" @click="batchUpdateStatus('selected')">Select All Selected</button>
        <button class="btn btn-reject-all" @click="batchUpdateStatus('rejected')">Reject All Selected</button>
      </div>
    </div>

    <!-- Candidates Table -->
    <div class="table-container">
      <table class="table">
        <thead>
          <tr>
            <th class="checkbox-column">
              <input type="checkbox" :checked="allSelected" @click="toggleAll" />
            </th>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Status</th>
            <th>Passing Year</th>
            <th>Round</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="candidate in candidates" :key="candidate.id">
            <td class="checkbox-column">
              <input type="checkbox" v-model="selectedCandidates" :value="candidate.id" />
            </td>
            <td>{{ candidate.id }}</td>
            <td>{{ candidate.name }}</td>
            <td>{{ candidate.email }}</td>
            <td>
              <span :class="{'status-selected': candidate.status === 'selected', 'status-rejected': candidate.status === 'rejected'}">
                {{ candidate.status }}
              </span>
            </td>
            <td>{{ candidate.year }}</td>
            <td>{{ candidate.round }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Compose Email Modal -->
    <div v-if="showComposeModal" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeComposeModal">&times;</span>
        <h2>Compose Email</h2>

        <!-- Status Selection -->
        <label for="emailStatus">Send to candidates with status:</label>
        <select id="emailStatus" v-model="emailStatus">
          <option value="">All</option>
          <option value="selected">Selected</option>
          <option value="pending">Pending</option>
          <option value="rejected">Rejected</option>
        </select>

        <!-- Subject Field -->
        <label for="emailSubject">Subject:</label>
        <input type="text" id="emailSubject" v-model="emailSubject" />

        <!-- Message Field -->
        <label for="emailBody">Message:</label>
        <textarea id="emailBody" v-model="emailBody"></textarea>

        <!-- Templates -->
        <p>Select an email template for the {{ roundLabel }} round (optional):</p>
        <div v-if="availableTemplates.length > 0">
          <ul class="template-list">
            <li v-for="template in availableTemplates" :key="template.id">
              <input
                type="radio"
                :id="template.id"
                v-model="selectedTemplateId"
                :value="template.id"
                @change="applyTemplate(template)"
              />
              <label :for="template.id">{{ template.subject }}</label>
            </li>
          </ul>
        </div>
        <div v-else>
          <p>No templates available for the selected round.</p>
        </div>

        <button class="btn btn-send-email" :disabled="!emailSubject || !emailBody" @click="sendEmails">Send Emails</button>
      </div>
    </div>

    <!-- Success and Error Notifications -->
    <div v-if="notification.message" :class="['notification', notification.type]">
      {{ notification.message }}
      <span class="close" @click="notification.message = ''">&times;</span>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

// Set the API URL from environment variable or fallback to localhost
const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:5000';

export default {
  data() {
    return {
      candidates: [],
      selectedCandidates: [],
      passingYear: '',
      round: '',
      showComposeModal: false,
      availableTemplates: [],
      selectedTemplateId: '',
      emailSubject: '',
      emailBody: '',
      emailStatus: '',
      notification: {
        message: '',
        type: ''
      }
    };
  },
  created() {
    this.fetchCandidates();
  },
  methods: {
    // Fetch candidates based on current filters
    fetchCandidates() {
      const params = {};
      if (this.passingYear) params.year = this.passingYear;
      if (this.round) params.round = this.round;

      axios
        .get(`${API_URL}/candidates`, { params })
        .then((response) => {
          this.candidates = response.data.candidates;
        })
        .catch((error) => {
          console.log('Error fetching candidates:', error);
          this.showNotification('Error fetching candidates.', 'error');
        });
    },
    // Open the compose email modal and fetch available templates
    openComposeModal() {
      if (!this.round) {
        this.showNotification('Please select an interview round to compose emails.', 'error');
        return;
      }

      this.emailSubject = '';
      this.emailBody = '';
      this.selectedTemplateId = '';
      this.emailStatus = '';

      axios
        .get(`${API_URL}/get_templates`, { params: { round: this.round } })
        .then((response) => {
          this.availableTemplates = response.data.templates;
          if (this.availableTemplates.length === 0) {
            this.showNotification('No templates available for the selected round.', 'error');
          }
          this.showComposeModal = true;
        })
        .catch((error) => {
          console.log('Error fetching templates:', error);
          this.showNotification('Error fetching templates.', 'error');
        });
    },
    // Close the compose email modal and reset selections
    closeComposeModal() {
      this.showComposeModal = false;
      this.availableTemplates = [];
      this.selectedTemplateId = '';
      this.emailSubject = '';
      this.emailBody = '';
      this.emailStatus = '';
    },
    // Apply selected template to subject and body
    applyTemplate(template) {
      this.emailSubject = template.subject;
      this.emailBody = template.body;
    },
    // Send emails using the subject, body, and status filter
    sendEmails() {
      if (!this.emailSubject || !this.emailBody) {
        this.showNotification('Please enter both subject and message to send emails.', 'error');
        return;
      }

      axios
        .post(`${API_URL}/send_emails_by_filter`, {
          year: this.passingYear,
          round: this.round,
          status: this.emailStatus,
          subject: this.emailSubject,
          body: this.emailBody
        })
        .then((response) => {
          this.showNotification(response.data.message, 'success');
          this.closeComposeModal();
          this.fetchCandidates();
        })
        .catch((error) => {
          console.log('Error sending emails:', error);
          if (error.response && error.response.data && error.response.data.error) {
            this.showNotification(`Error: ${error.response.data.error}`, 'error');
          } else {
            this.showNotification('An error occurred while sending emails.', 'error');
          }
        });
    },
    // Batch update status of selected candidates
    batchUpdateStatus(status) {
      if (this.selectedCandidates.length === 0) {
        this.showNotification('No candidates selected for batch update.', 'error');
        return;
      }

      const requests = this.selectedCandidates.map((id) =>
        axios.post(`${API_URL}/update_status/${id}`, { status })
      );

      Promise.all(requests)
        .then(() => {
          this.showNotification(`Candidates ${status} successfully.`, 'success');
          this.fetchCandidates();
          this.selectedCandidates = [];
        })
        .catch((error) => {
          console.log('Error updating status in batch:', error);
          this.showNotification('An error occurred while updating statuses.', 'error');
        });
    },
    // Toggle selection of all candidates
    toggleAll() {
      if (this.allSelected) {
        this.selectedCandidates = [];
      } else {
        this.selectedCandidates = this.candidates.map((candidate) => candidate.id);
      }
    },
    // Display notifications
    showNotification(message, type) {
      this.notification.message = message;
      this.notification.type = type;

      // Auto-hide notification after 5 seconds
      setTimeout(() => {
        this.notification.message = '';
        this.notification.type = '';
      }, 5000);
    }
  },
  computed: {
    // Determine if all candidates are selected
    allSelected: {
      get() {
        return this.selectedCandidates.length === this.candidates.length && this.candidates.length > 0;
      },
      set(value) {
        if (value) {
          this.selectedCandidates = this.candidates.map((candidate) => candidate.id);
        } else {
          this.selectedCandidates = [];
        }
      },
    },
    // Get label for the round (for display purposes)
    roundLabel() {
      const labels = {
        'level1': 'Level 1',
        'level2': 'Level 2',
        'final': 'Final'
      };
      return labels[this.round] || 'Selected';
    }
  },
};
</script>

<style scoped>
.app {
  max-width: 100%;
  padding: 20px;
  background-color: #f9f9f9;
  margin: 0;
}

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 25px;
}

.logo-container {
  margin-right: 15px;
}

.logo {
  height: 60px;
  width: auto;
}

.header-text {
  margin-left: 15px;
  flex-grow: 1;
}

h1 {
  font-size: 2rem;
  margin: 0 0 5px 0;
}

p {
  font-size: 1rem;
  margin: 0;
}

.filters-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 30px;
  gap: 15px;
}

.filters {
  display: flex;
  gap: 15px;
  align-items: center;
}

.batch-actions {
  display: flex;
  gap: 10px;
}

.compose-email-container-top {
}

.btn {
  padding: 8px 16px;
  margin: 0;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-select-all {
  background-color: #2ecc71;
  color: white;
}

.btn-reject-all {
  background-color: #e74c3c;
  color: white;
}

.btn-compose-email {
  background-color: #3498db;
  color: white;
}

.btn-send-email {
  background-color: #3498db;
  color: white;
  margin-top: 20px;
}

.table-container {
  margin-top: 20px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

th,
td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

th {
  background-color: #3498db;
  color: white;
}

.checkbox-column {
  width: 50px;
}

tr:hover {
  background-color: #f1f1f1;
}

.status-selected {
  color: green;
  font-weight: bold;
}

.status-rejected {
  color: red;
  font-weight: bold;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: #fff;
  padding: 30px;
  border-radius: 10px;
  width: 500px;
  max-width: 90%;
  position: relative;
}

.modal-content h2 {
  margin-top: 0;
}

.modal-content .close {
  position: absolute;
  top: 15px;
  right: 20px;
  font-size: 1.5rem;
  cursor: pointer;
}

.modal-content label {
  display: block;
  margin-top: 15px;
  font-weight: bold;
}

.modal-content select,
.modal-content input[type="text"],
.modal-content textarea {
  width: 100%;
  padding: 8px;
  margin-top: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.modal-content textarea {
  height: 150px;
  resize: vertical;
}

.template-list {
  list-style-type: none;
  padding: 0;
}

.template-list li {
  margin-bottom: 10px;
}

.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 5px;
  color: white;
  z-index: 1001;
}

.notification.success {
  background-color: #2ecc71;
}

.notification.error {
  background-color: #e74c3c;
}

.notification .close {
  margin-left: 15px;
  cursor: pointer;
  font-weight: bold;
}
</style>
