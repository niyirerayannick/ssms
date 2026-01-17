/**
 * Rwanda Location Hierarchy Manager
 * Handles cascading dropdown selections for Province -> District -> Sector -> Cell -> Village
 */

class RwandaLocationManager {
  constructor(options = {}) {
    this.apiBaseUrl = options.apiBaseUrl || '/core/api/locations';
    this.provinceSelector = options.provinceSelector || '#id_province';
    this.districtSelector = options.districtSelector || '#id_district';
    this.sectorSelector = options.sectorSelector || '#id_sector';
    this.cellSelector = options.cellSelector || '#id_cell';
    this.villageSelector = options.villageSelector || '#id_village';
    
    this.provinceElement = document.querySelector(this.provinceSelector);
    this.districtElement = document.querySelector(this.districtSelector);
    this.sectorElement = document.querySelector(this.sectorSelector);
    this.cellElement = document.querySelector(this.cellSelector);
    this.villageElement = document.querySelector(this.villageSelector);
    
    this.init();
  }
  
  init() {
    if (!this.provinceElement) return;
    
    // Load provinces on initialization
    this.loadProvinces();
    
    // Set up event listeners for cascading
    if (this.provinceElement) {
      this.provinceElement.addEventListener('change', () => this.onProvinceChange());
    }
    if (this.districtElement) {
      this.districtElement.addEventListener('change', () => this.onDistrictChange());
    }
    if (this.sectorElement) {
      this.sectorElement.addEventListener('change', () => this.onSectorChange());
    }
    if (this.cellElement) {
      this.cellElement.addEventListener('change', () => this.onCellChange());
    }
  }
  
  /**
   * Load all provinces
   */
  async loadProvinces() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/provinces/`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.populateSelect(this.provinceElement, data.data);
      }
    } catch (error) {
      console.error('Error loading provinces:', error);
    }
  }
  
  /**
   * Load districts for selected province
   */
  async onProvinceChange() {
    const provinceId = this.provinceElement.value;
    
    // Reset dependent selects
    this.clearSelect(this.districtElement);
    this.clearSelect(this.sectorElement);
    this.clearSelect(this.cellElement);
    this.clearSelect(this.villageElement);
    
    if (!provinceId) return;
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/districts/${provinceId}/`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.populateSelect(this.districtElement, data.data);
      }
    } catch (error) {
      console.error('Error loading districts:', error);
    }
  }
  
  /**
   * Load sectors for selected district
   */
  async onDistrictChange() {
    const districtId = this.districtElement.value;
    
    // Reset dependent selects
    this.clearSelect(this.sectorElement);
    this.clearSelect(this.cellElement);
    this.clearSelect(this.villageElement);
    
    if (!districtId) return;
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/sectors/${districtId}/`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.populateSelect(this.sectorElement, data.data);
      }
    } catch (error) {
      console.error('Error loading sectors:', error);
    }
  }
  
  /**
   * Load cells for selected sector
   */
  async onSectorChange() {
    const sectorId = this.sectorElement.value;
    
    // Reset dependent selects
    this.clearSelect(this.cellElement);
    this.clearSelect(this.villageElement);
    
    if (!sectorId) return;
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/cells/${sectorId}/`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.populateSelect(this.cellElement, data.data);
      }
    } catch (error) {
      console.error('Error loading cells:', error);
    }
  }
  
  /**
   * Load villages for selected cell
   */
  async onCellChange() {
    const cellId = this.cellElement.value;
    
    this.clearSelect(this.villageElement);
    
    if (!cellId) return;
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/villages/${cellId}/`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.populateSelect(this.villageElement, data.data);
      }
    } catch (error) {
      console.error('Error loading villages:', error);
    }
  }
  
  /**
   * Populate a select element with options
   */
  populateSelect(selectElement, options) {
    if (!selectElement) return;
    
    // Keep the default empty option
    const defaultOption = selectElement.querySelector('option[value=""]');
    selectElement.innerHTML = '';
    
    if (defaultOption) {
      selectElement.appendChild(defaultOption.cloneNode(true));
    } else {
      const emptyOption = document.createElement('option');
      emptyOption.value = '';
      emptyOption.textContent = '-- Select --';
      selectElement.appendChild(emptyOption);
    }
    
    // Add option for each item
    options.forEach(option => {
      const optionElement = document.createElement('option');
      optionElement.value = option.id;
      optionElement.textContent = option.name;
      selectElement.appendChild(optionElement);
    });
  }
  
  /**
   * Clear all options from a select element (except default)
   */
  clearSelect(selectElement) {
    if (!selectElement) return;
    
    const defaultOption = selectElement.querySelector('option[value=""]');
    selectElement.innerHTML = '';
    
    if (defaultOption) {
      selectElement.appendChild(defaultOption.cloneNode(true));
    } else {
      const emptyOption = document.createElement('option');
      emptyOption.value = '';
      emptyOption.textContent = '-- Select --';
      selectElement.appendChild(emptyOption);
    }
  }
  
  /**
   * Get full location path as object
   */
  getSelectedLocation() {
    return {
      province_id: this.provinceElement?.value || null,
      district_id: this.districtElement?.value || null,
      sector_id: this.sectorElement?.value || null,
      cell_id: this.cellElement?.value || null,
      village_id: this.villageElement?.value || null,
    };
  }
  
  /**
   * Set location values programmatically
   */
  async setLocation(provinceId, districtId = null, sectorId = null, cellId = null, villageId = null) {
    if (this.provinceElement && provinceId) {
      this.provinceElement.value = provinceId;
      await this.onProvinceChange();
      
      if (districtId && this.districtElement) {
        this.districtElement.value = districtId;
        await this.onDistrictChange();
        
        if (sectorId && this.sectorElement) {
          this.sectorElement.value = sectorId;
          await this.onSectorChange();
          
          if (cellId && this.cellElement) {
            this.cellElement.value = cellId;
            await this.onCellChange();
            
            if (villageId && this.villageElement) {
              this.villageElement.value = villageId;
            }
          }
        }
      }
    }
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = RwandaLocationManager;
}
