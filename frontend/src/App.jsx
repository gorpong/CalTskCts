import React, { useState, useEffect } from 'react';
import { Calendar, CheckSquare, Users, Plus, Search, Edit2, Trash2, X, Clock, Filter, ChevronLeft, ChevronRight, AlertTriangle, ArrowUpNarrowWide, ArrowDownWideNarrow, Loader2, Zap } from 'lucide-react';
const TASK_STATES = ['Not Started', 'In Progress', 'Completed', 'Canceled'];

const getTaskStateStyle = (state) => {
  switch(state) {
    case 'Not Started': return 'bg-slate-100 text-slate-700';
    case 'In Progress': return 'bg-amber-100 text-amber-700';
    case 'Completed': return 'bg-emerald-100 text-emerald-700';
    case 'Canceled': return 'bg-red-100 text-red-700';
    default: return 'bg-slate-100 text-slate-700';
  }
};

const api = {
  // Helper to handle responses and throw on errors
  async handleResponse(res) {
    const data = await res.json();
    if (!res.ok) {
      // Throw the error message from the backend, or a default message
      throw new Error(data.error || `Request failed with status ${res.status}`);
    }
    return data;
  },

  // Contacts
  async getContacts(query = '') {
    const url = query ? `/contacts?q=${encodeURIComponent(query)}` : '/contacts';
    const res = await fetch(url);
    return this.handleResponse(res);
  },
  async createContact(data) {
    const res = await fetch('/contacts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return this.handleResponse(res);
  },
  async updateContact(id, data) {
    const res = await fetch(`/contacts/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return this.handleResponse(res);
  },
  async deleteContact(id) {
    const res = await fetch(`/contacts/${id}`, { method: 'DELETE' });
    return this.handleResponse(res);
  },

  // Events
  async getEvents(params = {}) {
    let url = '/events';
    const queryParams = new URLSearchParams();
    if (params.date) queryParams.set('date', params.date);
    if (params.start && params.end) {
      queryParams.set('start', params.start);
      queryParams.set('end', params.end);
    }
    if (queryParams.toString()) url += `?${queryParams}`;
    const res = await fetch(url);
    return this.handleResponse(res);
  },
  async createEvent(data) {
    const res = await fetch('/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return this.handleResponse(res);
  },
  async updateEvent(id, data) {
    const res = await fetch(`/events/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return this.handleResponse(res);
  },
  async deleteEvent(id) {
    const res = await fetch(`/events/${id}`, { method: 'DELETE' });
    return this.handleResponse(res);
  },
  async findNextAvailable(start, duration) {
    const res = await fetch(`/events/next-available?start=${encodeURIComponent(start)}&duration=${duration}`);
    return this.handleResponse(res);
  },

  // Tasks
  async getTasks(params = {}) {
    let url = '/tasks';
    const queryParams = new URLSearchParams();
    if (params.state) queryParams.set('state', params.state);
    if (params.due_date) queryParams.set('due_date', params.due_date);
    if (params.min_progress) queryParams.set('min_progress', params.min_progress);
    if (params.max_progress) queryParams.set('max_progress', params.max_progress);
    if (queryParams.toString()) url += `?${queryParams}`;
    const res = await fetch(url);
    return this.handleResponse(res);
  },
  async createTask(data) {
    const res = await fetch('/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return this.handleResponse(res);
  },
  async updateTask(id, data) {
    const res = await fetch(`/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return this.handleResponse(res);
  },
  async deleteTask(id) {
    const res = await fetch(`/tasks/${id}`, { method: 'DELETE' });
    return this.handleResponse(res);
  }
};

// Date format conversion helpers
// Backend format: MM/DD/YYYY HH:MM (datetime) or MM/DD/YYYY (date)
// HTML input format: YYYY-MM-DDTHH:MM (datetime-local) or YYYY-MM-DD (date)

const dateHelpers = {
  // Convert MM/DD/YYYY HH:MM to YYYY-MM-DDTHH:MM
  toDateTimeLocal(backendDate) {
    if (!backendDate) return '';
    const [datePart, timePart] = backendDate.split(' ');
    if (!datePart) return '';
    const [month, day, year] = datePart.split('/');
    const time = timePart || '00:00';
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}T${time}`;
  },

  // Convert YYYY-MM-DDTHH:MM to MM/DD/YYYY HH:MM
  fromDateTimeLocal(localDate) {
    if (!localDate) return '';
    const [datePart, timePart] = localDate.split('T');
    const [year, month, day] = datePart.split('-');
    return `${month}/${day}/${year} ${timePart}`;
  },

  // Convert MM/DD/YYYY to YYYY-MM-DD
  toDateLocal(backendDate) {
    if (!backendDate) return '';
    const [month, day, year] = backendDate.split('/');
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  },

  // Convert YYYY-MM-DD to MM/DD/YYYY
  fromDateLocal(localDate) {
    if (!localDate) return '';
    const [year, month, day] = localDate.split('-');
    return `${month}/${day}/${year}`;
  }
};

const App = () => {
  const [activeTab, setActiveTab] = useState('calendar');
  const [contacts, setContacts] = useState([]);
  const [events, setEvents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState('checking');
  const [searchQuery, setSearchQuery] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('add');
  const [editItem, setEditItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [filters, setFilters] = useState({ states: [], dateFilter: '' });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState({ show: false, id: null, type: '', itemName: '' });
  const [progressSort, setProgressSort] = useState(null);

  const [showFindAvailable, setShowFindAvailable] = useState(false);
  const [findAvailableStart, setFindAvailableStart] = useState('');
  const [findAvailableDuration, setFindAvailableDuration] = useState(30);
  const [findAvailableResult, setFindAvailableResult] = useState(null);
  const [findAvailableLoading, setFindAvailableLoading] = useState(false);

  // For the in-modal version
  const [modalFindExpanded, setModalFindExpanded] = useState(false);
  const [modalFindStart, setModalFindStart] = useState('');
  const [modalFindDuration, setModalFindDuration] = useState(30);
  const [modalFindResult, setModalFindResult] = useState(null);
  const [modalFindLoading, setModalFindLoading] = useState(false);

  // Load data on mount and tab change
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'contacts') {
        const data = await api.getContacts();
        setContacts(Array.isArray(data) ? data : Object.values(data));
      } else if (activeTab === 'calendar') {
        const data = await api.getEvents();
        setEvents(Array.isArray(data) ? data : Object.values(data));
      } else if (activeTab === 'tasks') {
        const data = await api.getTasks();
        setTasks(Array.isArray(data) ? data : Object.values(data));
      }
      setApiStatus('connected');
    } catch (err) {
      console.error('Failed to load data:', err);
      setApiStatus('error');
    }
    setLoading(false);
  };

  const openAddModal = () => { 
    setModalType('add'); 
    setEditItem(null); 
    setFormData({});
    setShowModal(true); 
  };

  const openEditModal = (item) => { 
    setModalType('edit'); 
    setEditItem(item); 
    
    // Convert dates to HTML input format when editing
    const formDataWithConvertedDates = { ...item };
    
    if (activeTab === 'calendar' && item.date) {
      formDataWithConvertedDates.dateTimeLocal = dateHelpers.toDateTimeLocal(item.date);
    }
    
    if (activeTab === 'tasks' && item.dueDate) {
      formDataWithConvertedDates.dueDateLocal = dateHelpers.toDateLocal(item.dueDate);
    }
    
    setFormData(formDataWithConvertedDates);
    setShowModal(true); 
  };

  // Handler for header "Find Available" panel
  const handleFindAvailable = async () => {
    if (!findAvailableStart) {
      alert('Please select a starting date/time');
      return;
    }
    setFindAvailableLoading(true);
    try {
      const startFormatted = dateHelpers.fromDateTimeLocal(findAvailableStart);
      const result = await api.findNextAvailable(startFormatted, findAvailableDuration);
      setFindAvailableResult(result.available_time);
    } catch (err) {
      console.error('Find available failed:', err);
      alert(err.message || 'Failed to find available time.');
    }
    setFindAvailableLoading(false);
  };

  // Use the result from header panel and open Add modal
  const useFindAvailableResult = () => {
    setFormData({
      dateTimeLocal: dateHelpers.toDateTimeLocal(findAvailableResult),
      duration: findAvailableDuration
    });
    setShowFindAvailable(false);
    setFindAvailableResult(null);
    setModalType('add');
    setEditItem(null);
    setShowModal(true);
  };

  // Handler for in-modal "Find Available"
  const handleModalFindAvailable = async () => {
    if (!modalFindStart) {
      alert('Please select a starting date/time');
      return;
    }
    setModalFindLoading(true);
    try {
      const startFormatted = dateHelpers.fromDateTimeLocal(modalFindStart);
      const result = await api.findNextAvailable(startFormatted, modalFindDuration);
      setModalFindResult(result.available_time);
    } catch (err) {
      console.error('Find available failed:', err);
      alert(err.message || 'Failed to find available time.');
    }
    setModalFindLoading(false);
  };

  // Use the result from in-modal panel
  const useModalFindResult = () => {
    setFormData(prev => ({
      ...prev,
      dateTimeLocal: dateHelpers.toDateTimeLocal(modalFindResult),
      duration: modalFindDuration
    }));
    setModalFindExpanded(false);
    setModalFindResult(null);
  };

  // Reset modal find state when closing modal
  const closeModal = () => { 
    setShowModal(false); 
    setEditItem(null); 
    setFormData({});
    // Reset modal find available state
    setModalFindExpanded(false);
    setModalFindStart('');
    setModalFindDuration(30);
    setModalFindResult(null);
  };

  const getEntityName = (type) => {
    switch(type) {
      case 'calendar': return 'event';
      case 'contacts': return 'contact';
      case 'tasks': return 'task';
      default: return type.slice(0, -1);
    }
  };

  const handleFormChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    try {
      if (activeTab === 'contacts') {
        if (modalType === 'add') {
          await api.createContact(formData);
        } else {
          const { id, ...contactPayload } = formData;
          await api.updateContact(editItem.id, contactPayload);
        }
      } else if (activeTab === 'calendar') {
        // Convert dateTimeLocal back to backend format
        const { id, dateTimeLocal, ...eventFields } = formData;
        const eventData = {
          ...eventFields,
          date: dateHelpers.fromDateTimeLocal(dateTimeLocal),
          users: typeof eventFields.users === 'string' 
            ? eventFields.users.split(',').map(u => u.trim()).filter(Boolean)
            : eventFields.users || []
        };
        if (modalType === 'add') {
          await api.createEvent(eventData);
        } else {
          await api.updateEvent(editItem.id, eventData);
        }
      } else if (activeTab === 'tasks') {
        // Convert dueDateLocal back to backend format
        const { id, desc, dueDate, dueDateLocal, ...otherFields } = formData;
        const taskPayload = {
          ...otherFields,
          description: desc,
          due_date: dateHelpers.fromDateLocal(dueDateLocal)
        };
        if (modalType === 'add') {
          await api.createTask(taskPayload);
        } else {
          await api.updateTask(editItem.id, taskPayload);
        }
      }
      closeModal();
      loadData();
    } catch (err) {
      console.error('Save failed:', err);
      alert(err.message || 'Failed to save. Please try again.');
    }
  };

  const confirmDelete = (id, itemName) => {
    setDeleteConfirm({ show: true, id, type: activeTab, itemName });
  };

  const handleDelete = async () => {
    const { id, type } = deleteConfirm;
    try {
      if (type === 'contacts') await api.deleteContact(id);
      else if (type === 'calendar') await api.deleteEvent(id);
      else await api.deleteTask(id);
      setDeleteConfirm({ show: false, id: null, type: '', itemName: '' });
      loadData();
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Failed to delete. Please try again.');
    }
  };

  const cancelDelete = () => {
    setDeleteConfirm({ show: false, id: null, type: '', itemName: '' });
  };

  const setSort = (direction) => {
    setProgressSort(progressSort === direction ? null : direction);
  };

  const toggleStateFilter = (state) => {
    setFilters(prev => ({
      ...prev,
      states: prev.states.includes(state)
        ? prev.states.filter(s => s !== state)
        : [...prev.states, state]
    }));
  };

  const NavButton = ({ tab, icon: Icon, label }) => (
    <button
      onClick={() => setActiveTab(tab)}
      className={`flex items-center gap-3 w-full px-3 py-3 rounded-lg transition-all ${
        activeTab === tab 
          ? 'bg-teal-600 text-white shadow-md' 
          : 'text-slate-300 hover:bg-slate-700'
      } ${sidebarCollapsed ? 'justify-center' : ''}`}
      title={sidebarCollapsed ? label : ''}
    >
      <Icon size={20} />
      {!sidebarCollapsed && <span className="font-medium">{label}</span>}
    </button>
  );

  const ProgressBar = ({ progress }) => (
    <div className="w-full bg-slate-200 rounded-full h-2">
      <div 
        className={`h-2 rounded-full transition-all ${progress === 100 ? 'bg-emerald-500' : 'bg-teal-500'}`}
        style={{ width: `${progress}%` }}
      />
    </div>
  );

  // Filter and sort data
  const filteredContacts = contacts.filter(c => 
    `${c.first_name} ${c.last_name} ${c.email} ${c.company || ''}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredEvents = events.filter(e => {
    const matchesSearch = (e.title || '').toLowerCase().includes(searchQuery.toLowerCase());
    if (filters.dateFilter) {
      return matchesSearch && (e.date || '').startsWith(filters.dateFilter);
    }
    return matchesSearch;
  });

  const filteredTasks = tasks.filter(t => {
    const matchesSearch = (t.title || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesState = filters.states.length === 0 || filters.states.includes(t.state);
    return matchesSearch && matchesState;
  }).sort((a, b) => {
    if (progressSort === 'asc') return (a.progress || 0) - (b.progress || 0);
    if (progressSort === 'desc') return (b.progress || 0) - (a.progress || 0);
    return 0;
  });

  return (
    <div className="flex h-screen bg-slate-100">
      {/* Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-slate-800 p-4 flex flex-col transition-all duration-300 relative`}>
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="absolute -right-3 top-6 bg-slate-700 text-white p-1 rounded-full hover:bg-slate-600 shadow-md z-10"
        >
          {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
        
        <div className={`mb-8 ${sidebarCollapsed ? 'text-center' : ''}`}>
          {sidebarCollapsed ? (
            <h1 className="text-xl font-bold text-white">C</h1>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-white">CalTskCts</h1>
              <p className="text-slate-400 text-sm">Manage your day</p>
            </>
          )}
        </div>
        <nav className="space-y-2">
          <NavButton tab="calendar" icon={Calendar} label="Calendar" />
          <NavButton tab="tasks" icon={CheckSquare} label="Tasks" />
          <NavButton tab="contacts" icon={Users} label="Contacts" />
        </nav>
        <div className={`mt-auto pt-4 border-t border-slate-700 ${sidebarCollapsed ? 'text-center' : ''}`}>
          {!sidebarCollapsed && <div className="text-slate-400 text-xs">API Status</div>}
          <div className={`flex items-center gap-2 mt-1 ${sidebarCollapsed ? 'justify-center' : ''}`}>
            <div className={`w-2 h-2 rounded-full ${
              apiStatus === 'connected' ? 'bg-emerald-400' : 
              apiStatus === 'error' ? 'bg-red-400' : 'bg-amber-400'
            }`}></div>
            {!sidebarCollapsed && (
              <span className="text-slate-300 text-sm capitalize">{apiStatus}</span>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm px-6 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <h2 className="text-2xl font-semibold text-slate-800 capitalize">{activeTab}</h2>
            <div className="flex items-center gap-4 flex-wrap">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="text"
                  placeholder={`Search ${activeTab}...`}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 w-64"
                />
              </div>

              {activeTab === 'calendar' && (
                <button
                  onClick={() => setShowFindAvailable(!showFindAvailable)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors border ${
                    showFindAvailable 
                      ? 'bg-amber-100 text-amber-700 border-amber-300' 
                      : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <Zap size={18} />
                  Find Available
                </button>
              )}
              <button
                onClick={openAddModal}
                className="flex items-center gap-2 bg-teal-600 text-white px-4 py-2 rounded-lg hover:bg-teal-700 transition-colors"
              >
                <Plus size={18} />
                Add New
              </button>
            </div>
          </div>
          
          {/* Filters */}
          {activeTab === 'tasks' && (
            <div className="flex items-center gap-4 mt-4 flex-wrap">
              <Filter size={16} className="text-slate-500" />
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500">States:</span>
                <div className="flex gap-1.5 flex-wrap">
                  {TASK_STATES.map(state => (
                    <button
                      key={state}
                      onClick={() => toggleStateFilter(state)}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors border ${
                        filters.states.includes(state)
                          ? `${getTaskStateStyle(state)} border-current`
                          : 'bg-white text-slate-500 border-slate-300 hover:border-slate-400'
                      }`}
                    >
                      {state}
                    </button>
                  ))}
                </div>
                {filters.states.length > 0 && (
                  <button
                    onClick={() => setFilters(prev => ({ ...prev, states: [] }))}
                    className="text-slate-400 hover:text-slate-600 ml-1"
                    title="Clear filter"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
              <div className="flex items-center gap-1 border-l border-slate-300 pl-4">
                <span className="text-sm text-slate-500 mr-2">Sort:</span>
                <button
                  onClick={() => setSort('asc')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    progressSort === 'asc' ? 'bg-teal-100 text-teal-700' : 'text-slate-500 hover:bg-slate-100'
                  }`}
                  title="Sort ascending"
                >
                  <ArrowUpNarrowWide size={16} />
                  {progressSort === 'asc' && <span>Asc</span>}
                </button>
                <button
                  onClick={() => setSort('desc')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    progressSort === 'desc' ? 'bg-teal-100 text-teal-700' : 'text-slate-500 hover:bg-slate-100'
                  }`}
                  title="Sort descending"
                >
                  <ArrowDownWideNarrow size={16} />
                  {progressSort === 'desc' && <span>Desc</span>}
                </button>
              </div>
            </div>
          )}
          {activeTab === 'calendar' && (
            <div className="flex items-center gap-4 mt-4 flex-wrap">
              <Filter size={16} className="text-slate-500" />
              <input
                type="text"
                placeholder="Filter by date (MM/DD/YYYY)"
                value={filters.dateFilter}
                onChange={(e) => setFilters({...filters, dateFilter: e.target.value})}
                className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 w-48"
              />
            </div>
          )}

          {/* Find Next Available Open Slot */}
          {activeTab === 'calendar' && showFindAvailable && (
            <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
              <div className="flex items-center gap-2 mb-3">
                <Zap size={18} className="text-amber-600" />
                <h3 className="font-semibold text-amber-800">Find Next Available Time</h3>
              </div>
              <div className="flex items-end gap-4 flex-wrap">
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Starting From</label>
                  <input
                    type="datetime-local"
                    value={findAvailableStart}
                    onChange={(e) => setFindAvailableStart(e.target.value)}
                    className="border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Duration (min)</label>
                  <input
                    type="number"
                    min="1"
                    value={findAvailableDuration}
                    onChange={(e) => setFindAvailableDuration(parseInt(e.target.value) || 30)}
                    className="border border-slate-300 rounded-lg px-3 py-2 w-24 focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
                <button
                  onClick={handleFindAvailable}
                  disabled={findAvailableLoading}
                  className="bg-amber-500 text-white px-4 py-2 rounded-lg hover:bg-amber-600 transition-colors disabled:opacity-50"
                >
                  {findAvailableLoading ? 'Searching...' : 'Search'}
                </button>
                {findAvailableResult && (
                  <div className="flex items-center gap-3 ml-4 px-4 py-2 bg-white border border-emerald-300 rounded-lg">
                    <div>
                      <span className="text-sm text-slate-500">Available: </span>
                      <span className="font-semibold text-emerald-700">{findAvailableResult}</span>
                    </div>
                    <button
                      onClick={useFindAvailableResult}
                      className="text-sm bg-emerald-500 text-white px-3 py-1 rounded-md hover:bg-emerald-600"
                    >
                      Use This Time
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="animate-spin text-teal-600" size={48} />
            </div>
          ) : (
            <>
              {/* Contacts View */}
              {activeTab === 'contacts' && (
                <div className="grid gap-4">
                  {filteredContacts.map(contact => (
                    <div key={contact.id} className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-gradient-to-br from-teal-400 to-cyan-500 rounded-full flex items-center justify-center text-white font-semibold text-lg flex-shrink-0">
                            {(contact.first_name || '?')[0]}{(contact.last_name || '?')[0]}
                          </div>
                          <div>
                            <h3 className="font-semibold text-slate-800">{contact.first_name} {contact.last_name}</h3>
                            <p className="text-slate-500 text-sm">{contact.title}</p>
                            {contact.company && <p className="text-teal-600 text-sm">{contact.company}</p>}
                          </div>
                        </div>
                        <div className="flex gap-2 flex-shrink-0">
                          <button onClick={() => openEditModal(contact)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-slate-100 rounded-lg">
                            <Edit2 size={16} />
                          </button>
                          <button onClick={() => confirmDelete(contact.id, `${contact.first_name} ${contact.last_name}`)} className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
                        <div><span className="text-slate-400">Email: </span><span className="text-slate-700">{contact.email}</span></div>
                        {contact.work_phone && <div><span className="text-slate-400">Work: </span><span className="text-slate-700">{contact.work_phone}</span></div>}
                        {contact.mobile_phone && <div><span className="text-slate-400">Mobile: </span><span className="text-slate-700">{contact.mobile_phone}</span></div>}
                      </div>
                    </div>
                  ))}
                  {filteredContacts.length === 0 && (
                    <p className="text-center text-slate-500 py-8">No contacts found</p>
                  )}
                </div>
              )}

              {/* Calendar View */}
              {activeTab === 'calendar' && (
                <div className="grid gap-4">
                  {filteredEvents.map(event => (
                    <div key={event.id} className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow border-l-4 border-teal-500">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-slate-800">{event.title}</h3>
                          <div className="flex items-center gap-4 mt-2 text-sm text-slate-500 flex-wrap">
                            <span className="flex items-center gap-1">
                              <Calendar size={14} />
                              {event.date}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock size={14} />
                              {event.duration} min
                            </span>
                          </div>
                          {event.users && event.users.length > 0 && (
                            <div className="flex items-center gap-2 mt-3 flex-wrap">
                              <span className="text-slate-400 text-sm">Attendees:</span>
                              <div className="flex gap-1.5 flex-wrap">
                                {event.users.map((user, i) => (
                                  <span key={i} className="bg-cyan-100 text-cyan-700 px-2.5 py-0.5 rounded-full text-xs font-medium">{user}</span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="flex gap-2 flex-shrink-0 ml-4">
                          <button onClick={() => openEditModal(event)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-slate-100 rounded-lg">
                            <Edit2 size={16} />
                          </button>
                          <button onClick={() => confirmDelete(event.id, event.title)} className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                  {filteredEvents.length === 0 && (
                    <p className="text-center text-slate-500 py-8">No events found</p>
                  )}
                </div>
              )}

              {/* Tasks View */}
              {activeTab === 'tasks' && (
                <div className="grid gap-4">
                  {filteredTasks.map(task => (
                    <div key={task.id} className={`bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow ${task.state === 'Completed' || task.state === 'Canceled' ? 'opacity-75' : ''}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 flex-wrap">
                            <h3 className={`font-semibold ${task.state === 'Completed' ? 'text-slate-500 line-through' : task.state === 'Canceled' ? 'text-slate-400 line-through' : 'text-slate-800'}`}>{task.title}</h3>
                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getTaskStateStyle(task.state)}`}>
                              {task.state}
                            </span>
                          </div>
                          <p className="text-slate-500 text-sm mt-1">{task.desc}</p>
                          <div className="flex items-center gap-6 mt-3 flex-wrap">
                            <span className="text-sm text-slate-400">Due: {task.dueDate}</span>
                            <div className="flex items-center gap-2 flex-1 max-w-xs min-w-32">
                              <ProgressBar progress={task.progress || 0} />
                              <span className="text-sm text-slate-600 font-medium">{task.progress || 0}%</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2 flex-shrink-0 ml-4">
                          <button onClick={() => openEditModal(task)} className="p-2 text-slate-400 hover:text-teal-600 hover:bg-slate-100 rounded-lg">
                            <Edit2 size={16} />
                          </button>
                          <button onClick={() => confirmDelete(task.id, task.title)} className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                  {filteredTasks.length === 0 && (
                    <p className="text-center text-slate-500 py-8">No tasks found</p>
                  )}
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800">
                {modalType === 'add' ? 'Add New' : 'Edit'} {getEntityName(activeTab)}
              </h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              {activeTab === 'contacts' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <input placeholder="First Name" value={formData.first_name || ''} onChange={e => handleFormChange('first_name', e.target.value)} className="border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                    <input placeholder="Last Name" value={formData.last_name || ''} onChange={e => handleFormChange('last_name', e.target.value)} className="border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                  </div>
                  <input placeholder="Title" value={formData.title || ''} onChange={e => handleFormChange('title', e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                  <input placeholder="Company" value={formData.company || ''} onChange={e => handleFormChange('company', e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                  <input placeholder="Email" value={formData.email || ''} onChange={e => handleFormChange('email', e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <input placeholder="Work Phone" value={formData.work_phone || ''} onChange={e => handleFormChange('work_phone', e.target.value)} className="border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                    <input placeholder="Mobile Phone" value={formData.mobile_phone || ''} onChange={e => handleFormChange('mobile_phone', e.target.value)} className="border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                    <input placeholder="Home Phone" value={formData.home_phone || ''} onChange={e => handleFormChange('home_phone', e.target.value)} className="border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                  </div>
                </>
              )}

            {/* Calendar Modal Fields */}
            {activeTab === 'calendar' && (
              <>
                <input placeholder="Event Title" value={formData.title || ''} onChange={e => handleFormChange('title', e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-slate-600 mb-1">Date & Time</label>
                    <input 
                      type="datetime-local" 
                      value={formData.dateTimeLocal || ''} 
                      onChange={e => handleFormChange('dateTimeLocal', e.target.value)} 
                      className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-600 mb-1">Duration (minutes)</label>
                    <input 
                      placeholder="Duration" 
                      type="number" 
                      min="1"
                      value={formData.duration || ''} 
                      onChange={e => handleFormChange('duration', parseInt(e.target.value) || 0)} 
                      className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" 
                    />
                  </div>
                </div>

                {/* Find Available Time - Inline Expanding */}
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <div 
                    className="p-3 bg-slate-50 flex items-center justify-between cursor-pointer hover:bg-slate-100"
                    onClick={() => setModalFindExpanded(!modalFindExpanded)}
                  >
                    <span className="text-sm text-slate-600">Need to find an open time slot?</span>
                    <button className="flex items-center gap-1 text-sm text-amber-600 hover:text-amber-700 font-medium">
                      <Zap size={14} />
                      {modalFindExpanded ? 'Close' : 'Find Available Time'}
                    </button>
                  </div>
                  {modalFindExpanded && (
                    <div className="p-4 bg-amber-50 border-t border-amber-200 space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-600 mb-1">Starting From</label>
                          <input
                            type="datetime-local"
                            value={modalFindStart}
                            onChange={(e) => setModalFindStart(e.target.value)}
                            className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-600 mb-1">Duration (min)</label>
                          <input
                            type="number"
                            min="1"
                            value={modalFindDuration}
                            onChange={(e) => setModalFindDuration(parseInt(e.target.value) || 30)}
                            className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                          />
                        </div>
                      </div>
                      <button
                        onClick={handleModalFindAvailable}
                        disabled={modalFindLoading}
                        className="w-full bg-amber-500 text-white px-3 py-2 rounded-lg hover:bg-amber-600 transition-colors text-sm font-medium disabled:opacity-50"
                      >
                        {modalFindLoading ? 'Searching...' : 'Search'}
                      </button>
                      {modalFindResult && (
                        <div className="flex items-center justify-between p-2 bg-white border border-emerald-300 rounded-lg">
                          <div>
                            <span className="text-xs text-slate-500">Available: </span>
                            <span className="font-semibold text-emerald-700">{modalFindResult}</span>
                          </div>
                          <button
                            onClick={useModalFindResult}
                            className="text-xs bg-emerald-500 text-white px-2 py-1 rounded hover:bg-emerald-600"
                          >
                            Use This Time
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <input placeholder="Attendees (comma-separated)" value={Array.isArray(formData.users) ? formData.users.join(', ') : formData.users || ''} onChange={e => handleFormChange('users', e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
              </>
            )}

            {/* Tasks Modal Fields */}
            {activeTab === 'tasks' && (
              <>
                <input placeholder="Task Title" value={formData.title || ''} onChange={e => handleFormChange('title', e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                <textarea placeholder="Description" rows={3} value={formData.desc || ''} onChange={e => handleFormChange('desc', e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-slate-600 mb-1">Due Date</label>
                    <input 
                      type="date" 
                      value={formData.dueDateLocal || ''} 
                      onChange={e => handleFormChange('dueDateLocal', e.target.value)} 
                      className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-600 mb-1">State</label>
                    <select value={formData.state || 'Not Started'} onChange={e => handleFormChange('state', e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500">
                      {TASK_STATES.map(state => (
                        <option key={state} value={state}>{state}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Progress: {formData.progress || 0}%</label>
                  <input type="range" min="0" max="100" value={formData.progress || 0} onChange={e => handleFormChange('progress', parseInt(e.target.value))} className="w-full" />
                </div>
              </>
            )}

            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50 rounded-b-2xl">
              <button onClick={closeModal} className="px-4 py-2 text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">
                Cancel
              </button>
              <button onClick={handleSave} className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors">
                {modalType === 'add' ? 'Create' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="p-6 text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertTriangle className="text-red-500" size={32} />
              </div>
              <h3 className="text-xl font-semibold text-slate-800 mb-2">Confirm Delete</h3>
              <p className="text-slate-500 mb-2">
                Are you sure you want to delete this {getEntityName(deleteConfirm.type)}?
              </p>
              <p className="text-slate-800 font-semibold mb-2">"{deleteConfirm.itemName}"</p>
              <p className="text-slate-400 text-sm mb-6">This action cannot be undone.</p>
              <div className="flex justify-center gap-3">
                <button onClick={cancelDelete} className="px-6 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors border border-slate-300">
                  Cancel
                </button>
                <button onClick={handleDelete} className="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
