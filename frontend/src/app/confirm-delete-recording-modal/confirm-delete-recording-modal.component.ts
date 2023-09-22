import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ApiService } from '../api.service';
import { ToastService } from '../toast.service';

interface Recording {
  datetime: string;
  filename: string;
}

@Component({
  selector: 'app-confirm-delete-recording-modal',
  templateUrl: './confirm-delete-recording-modal.component.html',
  styleUrls: ['./confirm-delete-recording-modal.component.scss']
})
export class ConfirmDeleteRecordingModalComponent {
  @Input() file: Recording | undefined;

  constructor(private apiService: ApiService,
    private toastService: ToastService,
    public activeModal: NgbActiveModal) {}

  deleteFile() {
      this.apiService.deleteRecording(this.file!.datetime, this.file!.filename).subscribe({
        next: (response) => {
        this.toastService.show("Successfully deleted recording.", { classname: 'bg-success text-light', delay: 5000 });
          
          this.activeModal.close('Deleted');
        },
        error: (err) => {
          console.log('Error deleting recording:', err);
        this.toastService.show("Failed to delete recording.", { classname: 'bg-danger text-light', delay: 5000 });
        this.activeModal.close('Deleted');
        }
      });
  }
}
