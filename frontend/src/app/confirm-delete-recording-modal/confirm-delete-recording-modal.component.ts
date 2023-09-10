import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-confirm-delete-recording-modal',
  templateUrl: './confirm-delete-recording-modal.component.html',
  styleUrls: ['./confirm-delete-recording-modal.component.scss']
})
export class ConfirmDeleteRecordingModalComponent {
  @Input() file: any;

  constructor(public activeModal: NgbActiveModal) {}

  deleteFile() {
    this.activeModal.close('Deleted');
  }
}
