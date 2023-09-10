import { Component } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ConfirmDeleteRecordingModalComponent } from '../confirm-delete-recording-modal/confirm-delete-recording-modal.component';

@Component({
  selector: 'app-recordings',
  templateUrl: './recordings.component.html',
  styleUrls: ['./recordings.component.scss']
})
export class RecordingsComponent {
  files = [
    { filename: 'File 1', dateCreated: '2023-09-10' },
    { filename: 'File 2', dateCreated: '2023-09-11' },
  ];

  constructor(private modalService: NgbModal) {} // Inject NgbModal

  confirmDelete(file: any) {
    const modalRef = this.modalService.open(ConfirmDeleteRecordingModalComponent);

    modalRef.componentInstance.file = file; // Pass the file data to the modal
  }
}
