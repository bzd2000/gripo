<template>
  <q-page class="q-pa-md">
    <div class="stagger-in">
      <div class="page-title">Settings</div>
      <div class="page-subtitle">Backup &amp; data</div>

      <div style="margin-top: 24px;">
        <div class="section-title">Backup database</div>

        <div class="setting-row">
          <div class="setting-label">Backup location</div>
          <div class="setting-value">
            <template v-if="dbPath">
              <code>{{ dbPath }}</code>
            </template>
            <template v-else>
              <span style="color: var(--g-text-muted);">Not configured</span>
            </template>
          </div>
          <q-btn
            v-if="hasElectron"
            flat dense size="sm" label="Change"
            @click="pickPath"
          />
        </div>

        <div class="setting-row" v-if="hasElectron" style="margin-top: 16px;">
          <div class="setting-label">Restore from backup</div>
          <div class="setting-value">
            <span style="color: var(--g-text-dim); font-size: 0.75rem;">
              Replaces all current data with the backup contents.
            </span>
          </div>
          <q-btn
            flat dense size="sm" label="Restore" color="red-4"
            @click="confirmRestore"
          />
        </div>
      </div>
    </div>

    <q-dialog v-model="showRestoreDialog">
      <q-card class="command-palette" style="width: 400px;">
        <q-card-section>
          <div style="color: var(--g-text-bright); font-size: 0.9rem; font-weight: 700;">
            Restore from backup?
          </div>
        </q-card-section>
        <q-card-section style="color: var(--g-text-secondary); font-size: 0.82rem;">
          This will replace all current data with the contents of your backup file.
          This action cannot be undone.
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="grey-7" v-close-popup />
          <q-btn flat label="Restore" color="red-4" @click="doRestore" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { db } from 'src/db/database';

const hasElectron = ref(!!window.electronAPI);
const dbPath = ref<string | undefined>();
const showRestoreDialog = ref(false);

onMounted(async () => {
  if (window.electronAPI) {
    dbPath.value = await window.electronAPI.dbGetPath();
  }
});

async function pickPath() {
  if (!window.electronAPI) return;
  const newPath = await window.electronAPI.dbPickPath();
  if (newPath) {
    dbPath.value = newPath;
  }
}

function confirmRestore() {
  showRestoreDialog.value = true;
}

async function doRestore() {
  if (!window.electronAPI) return;
  showRestoreDialog.value = false;

  const data = await window.electronAPI.dbRestore();

  await db.transaction('rw', [db.subjects, db.tasks, db.agendaPoints, db.meetingMinutes], async () => {
    await db.subjects.clear();
    await db.tasks.clear();
    await db.agendaPoints.clear();
    await db.meetingMinutes.clear();

    if (data.subjects?.length) await db.subjects.bulkAdd(data.subjects as never[]);
    if (data.tasks?.length) await db.tasks.bulkAdd(data.tasks as never[]);
    if (data.agendaPoints?.length) await db.agendaPoints.bulkAdd(data.agendaPoints as never[]);
    if (data.meetingMinutes?.length) await db.meetingMinutes.bulkAdd(data.meetingMinutes as never[]);
  });

  window.location.reload();
}
</script>
