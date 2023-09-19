import { Component } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ConfirmDeleteRecordingModalComponent } from '../confirm-delete-recording-modal/confirm-delete-recording-modal.component';
import { ApiService } from '../api.service';
import { LoaderService } from '../loader.service';

interface Recording {
  datetime: string;
  filename: string;
}

@Component({
  selector: 'app-recordings',
  templateUrl: './recordings.component.html',
  styleUrls: ['./recordings.component.scss']
})
export class RecordingsComponent {
  files: Recording[] = [];
  currentPage = 1;
  itemsPerPage = 10;
  totalItems: number = 0;

  constructor(
    private modalService: NgbModal,
    private apiService: ApiService,
    private loaderService: LoaderService
  ) {}

  ngOnInit(): void {
    this.fetchRecordings();
  }

  viewVideo(file: Recording): void {
    const url = `http://localhost:8000/api/v1/stream?datetime=${file.datetime}&filename=${file.filename}`;
    window.open(url, '_blank');
  }

  fetchRecordings(): void {
    this.loaderService.show();

    this.apiService.getRecordings().subscribe((response) => {
      this.files = response.files;
      this.totalItems = this.files.length;

      this.loaderService.hide();
    });
  }

  get displayedFiles(): Recording[] {
    const start = (this.currentPage - 1) * this.itemsPerPage;
    const end = start + this.itemsPerPage;
    return this.files.slice(start, end);
  }

  nextPage(): void {
    if (this.currentPage * this.itemsPerPage < this.totalItems) {
      this.currentPage++;
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
    }
  }

  get totalPages(): number {
    return Math.ceil(this.totalItems / this.itemsPerPage);
  }

  firstPage(): void {
    this.currentPage = 1;
  }

  lastPage(): void {
    this.currentPage = this.totalPages;
  }

  confirmDelete(file: Recording): void {
    const modalRef = this.modalService.open(ConfirmDeleteRecordingModalComponent);
    modalRef.componentInstance.file = file;
  }
}
